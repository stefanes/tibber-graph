"""Shared helper functions for test scripts (ui_test and local_render).

This module provides common functionality for:
- Loading and parsing price data from JSON files
- Date mapping (test dates to relative dates: yesterday/today/tomorrow)
- Filtering based on start_graph_at settings
"""
import datetime
import json
from typing import Dict, List, Tuple, Optional

from dateutil import parser, tz


# Reuse local timezone object
LOCAL_TZ = tz.tzlocal()


def parse_time_string(time_str: str, reference_date: datetime.date) -> Optional[datetime.datetime]:
    """Parse a time string (HH:MM or HH:MM:SS) into a datetime on the reference date.

    Args:
        time_str: Time string in format "HH:MM" or "HH:MM:SS"
        reference_date: Date to apply the parsed time to

    Returns:
        datetime object with local timezone, or None if parsing fails
    """
    try:
        time_parts = time_str.strip().split(":")
        if len(time_parts) == 2:
            hour, minute = int(time_parts[0]), int(time_parts[1])
            second = 0
        elif len(time_parts) == 3:
            hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
        else:
            return None

        return datetime.datetime(
            reference_date.year,
            reference_date.month,
            reference_date.day,
            hour,
            minute,
            second,
            tzinfo=LOCAL_TZ
        )
    except (ValueError, AttributeError):
        return None


def create_date_mapping(
    sorted_dates: List[datetime.date],
    reference_date: datetime.date
) -> Dict[datetime.date, datetime.date]:
    """Create mapping from JSON dates to relative dates (yesterday/today/tomorrow).

    Args:
        sorted_dates: Sorted list of unique dates found in JSON data
        reference_date: Reference date to use as "today"

    Returns:
        Dictionary mapping original dates to relative dates
    """
    today = reference_date
    tomorrow = today + datetime.timedelta(days=1)
    yesterday = today - datetime.timedelta(days=1)

    date_mapping = {}

    if len(sorted_dates) >= 3:
        # 3+ days: treat as yesterday, today, tomorrow (and beyond if more)
        date_mapping[sorted_dates[0]] = yesterday
        date_mapping[sorted_dates[1]] = today
        date_mapping[sorted_dates[2]] = tomorrow
        # Map any additional days sequentially
        for i in range(3, len(sorted_dates)):
            date_mapping[sorted_dates[i]] = tomorrow + datetime.timedelta(days=i-2)
    elif len(sorted_dates) == 2:
        # 2 days: treat as today and tomorrow
        date_mapping[sorted_dates[0]] = today
        date_mapping[sorted_dates[1]] = tomorrow
    elif len(sorted_dates) == 1:
        # 1 day: treat as today
        date_mapping[sorted_dates[0]] = today

    return date_mapping


def should_include_date(
    mapped_date: datetime.date,
    reference_date: datetime.date,
    start_graph_at: Optional[str] = None,
    include_all: bool = False
) -> bool:
    """Determine if a date should be included based on filtering rules.

    Args:
        mapped_date: The date after mapping (relative to reference date)
        reference_date: Reference date to use as "today"
        start_graph_at: Optional start_graph_at setting ('show_all', 'midnight', 'current_hour')
        include_all: If True, include all dates regardless of other settings

    Returns:
        True if the date should be included, False otherwise
    """
    if include_all or start_graph_at == 'show_all':
        # Include all dates
        return True

    # Default: only include today and tomorrow (filter out yesterday)
    today = reference_date
    tomorrow = today + datetime.timedelta(days=1)
    return mapped_date in (today, tomorrow)


def parse_price_entry(
    entry: dict,
    date_mapping: Dict[datetime.date, datetime.date],
    reference_date: datetime.date,
    start_graph_at: Optional[str] = None,
    include_all: bool = False
) -> Optional[Tuple[datetime.datetime, float]]:
    """Parse a single price entry from JSON and apply date mapping/filtering.

    Args:
        entry: JSON entry with 'start_time' and 'price' fields
        date_mapping: Mapping of original dates to relative dates
        reference_date: Reference date to use as "today"
        start_graph_at: Optional start_graph_at setting
        include_all: If True, include all dates regardless of filtering

    Returns:
        Tuple of (datetime, price) if entry should be included, None otherwise
    """
    try:
        # Parse the timestamp from JSON
        dt = parser.isoparse(entry['start_time'])
        # Convert to local timezone
        dt_local = dt.astimezone(LOCAL_TZ)

        # Update the date based on mapping
        original_date = dt_local.date()
        if original_date not in date_mapping:
            # Unexpected date - skip it
            return None

        mapped_date = date_mapping[original_date]

        # Check if this date should be included
        if not should_include_date(mapped_date, reference_date, start_graph_at, include_all):
            return None

        # Apply the mapped date
        dt_local = dt_local.replace(year=mapped_date.year, month=mapped_date.month, day=mapped_date.day)

        # Extract price
        price = float(entry['price'])

        return (dt_local, price)
    except (KeyError, ValueError, TypeError):
        # Invalid entry - skip it
        return None


def load_price_data_from_json(
    json_file_path: str,
    reference_date: datetime.date,
    start_graph_at: Optional[str] = None,
    include_all: bool = False
) -> Tuple[List[datetime.datetime], List[float], Dict[datetime.date, datetime.date]]:
    """Load and process price data from JSON file.

    Args:
        json_file_path: Path to JSON file with price data
        reference_date: Reference date to use as "today"
        start_graph_at: Optional start_graph_at setting ('show_all', 'midnight', 'current_hour')
        include_all: If True, include all dates regardless of other settings

    Returns:
        Tuple of (dates, prices, date_mapping) where:
        - dates: List of datetime objects (localized and date-mapped)
        - prices: List of price values
        - date_mapping: Dictionary showing original -> mapped date conversions
    """
    # Load from JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            price_data_json = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load price data from {json_file_path}: {e}")

    # Find unique dates in the JSON data
    unique_dates = set()
    for entry in price_data_json:
        dt = parser.isoparse(entry['start_time'])
        unique_dates.add(dt.date())

    # Sort dates to establish mapping
    sorted_dates = sorted(unique_dates)

    # Create date mapping
    date_mapping = create_date_mapping(sorted_dates, reference_date)

    # Parse all entries
    dates = []
    prices = []
    for entry in price_data_json:
        result = parse_price_entry(entry, date_mapping, reference_date, start_graph_at, include_all)
        if result:
            dt_local, price = result
            dates.append(dt_local)
            prices.append(price)

    return dates, prices, date_mapping

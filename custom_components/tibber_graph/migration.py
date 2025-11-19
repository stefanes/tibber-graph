"""Migration utilities for Tibber Graph configuration options.

This module contains functions to migrate deprecated configuration options
to their new equivalents, ensuring backward compatibility across versions.
"""
import logging

from .const import (
    CONF_START_GRAPH_AT,
    CONF_THEME,
    CONF_TRANSPARENT_BACKGROUND,
    CONF_LABEL_CURRENT,
    CONF_LABEL_MAX,
    CONF_LABEL_MIN,
    CONF_SHOW_X_AXIS,
    CONF_SHOW_Y_AXIS,
    CONF_CHEAP_PERIODS_ON_X_AXIS,
    CONF_REFRESH_MODE,
    START_GRAPH_AT_MIDNIGHT,
    START_GRAPH_AT_CURRENT_HOUR,
    LABEL_CURRENT_ON,
    LABEL_CURRENT_ON_CURRENT_PRICE_ONLY,
    LABEL_CURRENT_ON_IN_GRAPH,
    LABEL_CURRENT_OFF,
    LABEL_MAX_ON,
    LABEL_MAX_ON_NO_PRICE,
    LABEL_MAX_OFF,
    LABEL_MIN_ON,
    LABEL_MIN_ON_NO_PRICE,
    LABEL_MIN_OFF,
    SHOW_X_AXIS_ON,
    SHOW_X_AXIS_ON_WITH_TICK_MARKS,
    SHOW_Y_AXIS_ON,
    SHOW_Y_AXIS_ON_WITH_TICK_MARKS,
    SHOW_Y_AXIS_OFF,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMFY,
    CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT,
    CHEAP_PERIODS_ON_X_AXIS_OFF,
    REFRESH_MODE_SYSTEM,
    REFRESH_MODE_SYSTEM_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# Legacy constants (for migration only)
CONF_LABEL_CURRENT_IN_HEADER = "label_current_in_header"
LABEL_CURRENT_IN_HEADER_ON = "on"
LABEL_CURRENT_IN_HEADER_OFF = "off"
LABEL_CURRENT_IN_HEADER_ON_CURRENT_PRICE_ONLY = "on_current_price_only"

# Legacy Y-axis constants (for migration only)
CONF_SHOW_Y_AXIS_TICK_MARKS = "show_y_axis_tick_marks"

# Legacy X-axis constants (for migration only)
CONF_CHEAP_PRICE_ON_X_AXIS = "cheap_price_on_x_axis"
CONF_CHEAP_LABELS_IN_SEPARATE_ROW = "cheap_labels_in_separate_row"

# Legacy refresh constants (for migration only)
CONF_AUTO_REFRESH_ENABLED = "auto_refresh_enabled"


def _get_value(entry, options, key):
    """Helper to retrieve value from options or entry.data.

    Args:
        entry: Config entry to check
        options: Current options dictionary
        key: Option key name

    Returns:
        Value from options or entry.data, or None if not found
    """
    if options and key in options:
        return options[key]
    if entry and key in entry.data:
        return entry.data[key]
    return None


def _get_old_value(entry, options, old_key):
    """Helper to retrieve old value from options or entry.data with location info.

    Args:
        entry: Config entry to check
        options: Current options dictionary
        old_key: Old option key name

    Returns:
        tuple: (has_value, value, location) where location is 'options' or 'data'
    """
    # Reuse _get_value to avoid duplication
    value = _get_value(entry, options, old_key)
    if value is not None:
        location = "options" if (options and old_key in options) else "data"
        return True, value, location
    return False, None, None


def _update_config_entry(hass, entry, options, new_options, keys_to_remove):
    """Helper to update config entry and remove old keys.

    Args:
        hass: Home Assistant instance
        entry: Config entry to update
        options: Original options dictionary
        new_options: Updated options dictionary
        keys_to_remove: List of old keys to remove

    Returns:
        dict: Updated options dictionary
    """
    # Remove old keys from the dict we're updating
    for key in keys_to_remove:
        if key in new_options:
            del new_options[key]

    # Update the config entry
    hass.config_entries.async_update_entry(entry, options=new_options)
    return new_options


def _cleanup_orphaned_option(hass, entry, options, name, old_key):
    """Clean up a single orphaned option.

    Args:
        hass: Home Assistant instance
        entry: Config entry to update
        options: Current options dictionary
        name: Entity name for logging
        old_key: Key of the orphaned option

    Returns:
        tuple: (cleanup_occurred, updated_options)
    """
    if old_key in (options or {}):
        _LOGGER.info(
            "Removing orphaned %s option from options for %s",
            old_key, name
        )
        new_options = dict(options) if options else {}
        del new_options[old_key]
        hass.config_entries.async_update_entry(entry, options=new_options)
        return True, new_options
    return False, options


def _migrate_boolean_to_dropdown(hass, entry, options, name, old_key, new_key, true_value, false_value):
    """Helper function to migrate a boolean option to a dropdown option.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging
        old_key: Old option key name
        new_key: New option key name
        true_value: Value to use when old option is True
        false_value: Value to use when old option is False

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    if not entry:
        return options

    has_old_option, old_value, location = _get_old_value(entry, options, old_key)

    # Only migrate if old option exists and new option doesn't
    if has_old_option and new_key not in (options or {}):
        new_value = true_value if old_value else false_value

        _LOGGER.info(
            "Migrating '%s' option for '%s': %s=%s → %s=%s",
            location, name, old_key, old_value, new_key, new_value
        )

        new_options = dict(options) if options else {}
        new_options[new_key] = new_value
        return _update_config_entry(hass, entry, options, new_options, [old_key])

    return options


def migrate_start_graph_at_option(hass, entry, options, name):
    """Migrate old 'start_at_midnight' boolean option to new 'start_graph_at' dropdown.

    This function converts the deprecated boolean option to the new dropdown format:
    - start_at_midnight=True → start_graph_at="midnight"
    - start_at_midnight=False → start_graph_at="current_hour"

    The migration is performed only once when the old option exists.
    After migration, the old option is removed from the config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    return _migrate_boolean_to_dropdown(
        hass, entry, options, name,
        "start_at_midnight", CONF_START_GRAPH_AT,
        START_GRAPH_AT_MIDNIGHT, START_GRAPH_AT_CURRENT_HOUR
    )


def migrate_dark_black_theme(hass, entry, options, name):
    """Migrate old 'dark_black' theme to 'dark' with transparent background.

    This function converts the deprecated dark_black theme to the new format:
    - theme="dark_black" → theme="dark" + transparent_background=True

    The migration is performed only once when the old theme value exists.
    After migration, the theme is updated and transparent_background is set.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    if not entry:
        return options

    # Check if theme is set to dark_black in either options or data
    has_dark_black = False
    location = None

    # Check options first (priority)
    if options and options.get(CONF_THEME) == "dark_black":
        has_dark_black = True
        location = "options"
    # Then check entry.data
    elif entry.data.get(CONF_THEME) == "dark_black":
        has_dark_black = True
        location = "data"

    # Only migrate if dark_black theme is found
    if has_dark_black:
        _LOGGER.info(
            "Migrating '%s' for '%s': theme='dark_black' → theme='dark' + transparent_background=True",
            location, name
        )

        # Update the config entry
        new_options = dict(options) if options else {}
        new_data = dict(entry.data)

        # Set theme to dark and enable transparent background
        if location == "options":
            new_options[CONF_THEME] = "dark"
            new_options[CONF_TRANSPARENT_BACKGROUND] = True
        else:  # location == "data"
            new_data[CONF_THEME] = "dark"
            # Add transparent background to options if not already there
            if CONF_TRANSPARENT_BACKGROUND not in new_options:
                new_options[CONF_TRANSPARENT_BACKGROUND] = True

        # Update the config entry
        hass.config_entries.async_update_entry(
            entry,
            data=new_data,
            options=new_options
        )

        return new_options

    return options


def migrate_label_current_option(hass, entry, options, name):
    """Migrate old 'label_current_at_top' option to new 'label_current_in_header'.

    This function renames the option from the old name to the new name:
    - label_current_at_top → label_current_in_header

    The migration is performed only once when the old option exists.
    After migration, the old option is removed from the config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    return _migrate_option_rename(
        hass, entry, options, name,
        "label_current_at_top", CONF_LABEL_CURRENT_IN_HEADER
    )


def _migrate_option_rename(hass, entry, options, name, old_key, new_key):
    """Helper function to migrate an option by renaming it.

    This function renames the option from old_key to new_key.
    The migration is performed only once when the old option exists.
    After migration, the old option is removed from the config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging
        old_key: Old option key name
        new_key: New option key name

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    if not entry:
        return options

    has_old_option, old_value, location = _get_old_value(entry, options, old_key)

    # Only migrate if old option exists and new option doesn't
    if has_old_option and new_key not in (options or {}):
        _LOGGER.info(
            "Migrating '%s' option for '%s': %s=%s → %s=%s",
            location, name, old_key, old_value, new_key, old_value
        )

        new_options = dict(options) if options else {}
        new_options[new_key] = old_value
        return _update_config_entry(hass, entry, options, new_options, [old_key])

    return options


def migrate_show_x_axis_tick_marks_option(hass, entry, options, name):
    """Migrate old 'show_x_axis_tick_marks' boolean option to new 'show_x_axis' dropdown.

    This function converts the deprecated boolean option to the new dropdown format:
    - show_x_axis_tick_marks=False → show_x_axis="on"
    - show_x_axis_tick_marks=True → show_x_axis="on_with_tick_marks"

    The migration is performed only once when the old option exists.
    After migration, the old option is removed from the config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    return _migrate_boolean_to_dropdown(
        hass, entry, options, name,
        "show_x_axis_tick_marks", CONF_SHOW_X_AXIS,
        SHOW_X_AXIS_ON_WITH_TICK_MARKS, SHOW_X_AXIS_ON
    )


def migrate_label_current_and_header_merge(hass, entry, options, name):
    """Migrate old boolean 'label_current', 'label_current_in_header', and 'label_current_in_header_more' to new dropdown.

    This function handles the complete migration of these three related options into a single
    'label_current' dropdown option. It handles all combinations of the old options:

    For label_current (old boolean):
    - label_current=False → label_current="off"
    - label_current=True + label_current_in_header=False → label_current="on_in_graph"
    - label_current=True + label_current_in_header=True + label_current_in_header_more=False → label_current="on_current_price_only"
    - label_current=True + label_current_in_header=True + label_current_in_header_more=True → label_current="on"

    The migration is performed when any of the old boolean options (label_current, label_current_in_header,
    or label_current_in_header_more) exist. Options not explicitly set use their old default values
    (label_current=True, label_current_in_header=True, label_current_in_header_more=True).
    After migration, both label_current_in_header and label_current_in_header_more options are removed.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    if entry is None:
        return options

    old_key_label_current = CONF_LABEL_CURRENT
    old_key_label_current_in_header = "label_current_in_header"
    old_key_label_current_in_header_more = "label_current_in_header_more"

    # Check if we have old related options that indicate this needs migration
    def _has_old_related_options():
        header_more = _get_value(entry, options, old_key_label_current_in_header_more)
        if header_more is not None:
            return True
        header = _get_value(entry, options, old_key_label_current_in_header)
        return isinstance(header, bool)

    # Determine if migration is needed and get label_current value
    label_current = _get_value(entry, options, old_key_label_current)

    if isinstance(label_current, bool):
        # Explicit boolean value found
        old_value_label_current = label_current
        location = "options" if options and old_key_label_current in options else "data"
    elif _has_old_related_options():
        # Old related options exist but label_current not explicitly set - use default
        old_value_label_current = True  # Old default value
        location = "default"
    else:
        # No migration needed - cleanup orphaned options if any
        return _cleanup_orphaned_options(hass, entry, options, name,
                                        old_key_label_current_in_header,
                                        old_key_label_current_in_header_more)

    # Get related option values
    old_value_label_current_in_header = _get_value(entry, options, old_key_label_current_in_header)
    old_value_label_current_in_header_more = _get_value(entry, options, old_key_label_current_in_header_more)

    # Determine new value based on old options
    new_value = _determine_new_label_current_value(
        old_value_label_current,
        old_value_label_current_in_header,
        old_value_label_current_in_header_more
    )

    _LOGGER.info(
        "Migrating '%s' options for '%s': %s=%s + %s=%s + %s=%s → %s=%s",
        location, name,
        old_key_label_current, old_value_label_current,
        old_key_label_current_in_header, old_value_label_current_in_header,
        old_key_label_current_in_header_more, old_value_label_current_in_header_more,
        old_key_label_current, new_value
    )

    new_options = dict(options) if options else {}
    new_options[CONF_LABEL_CURRENT] = new_value
    return _update_config_entry(hass, entry, options, new_options,
                               [old_key_label_current_in_header, old_key_label_current_in_header_more])


def _cleanup_orphaned_options(hass, entry, options, name, old_key_label_current_in_header, old_key_label_current_in_header_more):
    """Clean up orphaned label_current_in_header options.

    Args:
        hass: Home Assistant instance
        entry: Config entry to update
        options: Current options dictionary
        name: Entity name for logging
        old_key_label_current_in_header: Key for label_current_in_header option
        old_key_label_current_in_header_more: Key for label_current_in_header_more option

    Returns:
        dict: Updated options if cleanup occurred, otherwise original options
    """
    needs_cleanup = False
    new_options = dict(options) if options else {}

    # Check for orphaned label_current_in_header_more
    if old_key_label_current_in_header_more in new_options:
        _LOGGER.info(
            "Removing orphaned %s option from options for %s",
            old_key_label_current_in_header_more, name
        )
        del new_options[old_key_label_current_in_header_more]
        needs_cleanup = True

    # Check for orphaned label_current_in_header (only if it's still a boolean or old dropdown value)
    old_header_value = new_options.get(old_key_label_current_in_header)
    if old_header_value is not None and (
        isinstance(old_header_value, bool) or
        old_header_value in [LABEL_CURRENT_IN_HEADER_ON, LABEL_CURRENT_IN_HEADER_OFF, LABEL_CURRENT_IN_HEADER_ON_CURRENT_PRICE_ONLY]
    ):
        _LOGGER.info(
            "Removing orphaned %s option from options for %s (value=%s)",
            old_key_label_current_in_header, name, old_header_value
        )
        del new_options[old_key_label_current_in_header]
        needs_cleanup = True

    if needs_cleanup:
        hass.config_entries.async_update_entry(entry, options=new_options)
        return new_options

    return options


def _determine_new_label_current_value(label_current, label_current_in_header, label_current_in_header_more):
    """Determine the new label_current dropdown value based on old boolean options.

    Args:
        label_current: Old label_current boolean value
        label_current_in_header: Old label_current_in_header value (boolean, dropdown string, or None)
        label_current_in_header_more: Old label_current_in_header_more boolean value or None

    Returns:
        str: New label_current dropdown value
    """
    # If label_current is False, always return "off"
    if not label_current:
        return LABEL_CURRENT_OFF

    # Handle boolean or None (default) for label_current_in_header
    if isinstance(label_current_in_header, bool) or (label_current_in_header is None and label_current_in_header_more is not None):
        # Old boolean format (or None meaning default True)
        if label_current_in_header is False:
            return LABEL_CURRENT_ON_IN_GRAPH

        # label_current_in_header is True (or None = default True)
        # Check label_current_in_header_more (None = default True)
        if label_current_in_header_more is False:
            return LABEL_CURRENT_ON_CURRENT_PRICE_ONLY
        return LABEL_CURRENT_ON

    # label_current_in_header is already migrated to dropdown format or is None without label_current_in_header_more
    if label_current_in_header == LABEL_CURRENT_IN_HEADER_OFF or label_current_in_header is None:
        return LABEL_CURRENT_ON_IN_GRAPH
    if label_current_in_header == LABEL_CURRENT_IN_HEADER_ON_CURRENT_PRICE_ONLY:
        return LABEL_CURRENT_ON_CURRENT_PRICE_ONLY

    # LABEL_CURRENT_IN_HEADER_ON or any other value
    return LABEL_CURRENT_ON


def _migrate_boolean_with_secondary_to_dropdown(hass, entry, options, name, old_primary_key, secondary_key,
                                                primary_default, secondary_default, value_map,
                                                new_primary_key=None, remove_secondary=False):
    """Generic helper to migrate boolean with secondary option to dropdown.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging
        old_primary_key: Old primary option key (boolean)
        secondary_key: Secondary option key
        primary_default: Default value for primary option
        secondary_default: Default value for secondary option
        value_map: Dict mapping (primary_bool, secondary_value) to new dropdown value
        new_primary_key: New primary option key (if None, uses old_primary_key)
        remove_secondary: Whether to remove the secondary key after migration

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    if entry is None:
        return options

    # If no new key specified, use the old key (in-place migration)
    if new_primary_key is None:
        new_primary_key = old_primary_key

    # Get current values
    primary_value = _get_value(entry, options, old_primary_key)
    secondary_value = _get_value(entry, options, secondary_key)

    # Determine if migration is needed
    if isinstance(primary_value, bool):
        old_primary_value = primary_value
        location = "options" if options and old_primary_key in options else "data"
    elif secondary_value is not None:
        # Secondary exists but primary not explicitly set - use default
        old_primary_value = primary_default
        location = "default"
    else:
        # No migration needed - cleanup orphaned secondary if exists
        if remove_secondary and secondary_key in (options or {}):
            return _cleanup_orphaned_option(hass, entry, options, name, secondary_key)[1]
        return options

    # Get secondary value (use default if not set)
    if secondary_value is None:
        secondary_value = secondary_default

    # Determine new value based on value_map
    new_value = value_map.get((old_primary_value, secondary_value))
    if new_value is None:
        _LOGGER.warning(
            "No mapping found for %s=%s + %s=%s, skipping migration for %s",
            old_primary_key, old_primary_value, secondary_key, secondary_value, name
        )
        return options

    _LOGGER.info(
        "Migrating '%s' options for '%s': %s=%s + %s=%s → %s=%s",
        location, name,
        old_primary_key, old_primary_value,
        secondary_key, secondary_value,
        new_primary_key, new_value
    )

    new_options = dict(options) if options else {}
    new_options[new_primary_key] = new_value

    # Build list of keys to remove
    keys_to_remove = [secondary_key] if remove_secondary else []
    if old_primary_key != new_primary_key:
        keys_to_remove.append(old_primary_key)

    if keys_to_remove:
        return _update_config_entry(hass, entry, options, new_options, keys_to_remove)
    else:
        hass.config_entries.async_update_entry(entry, options=new_options)
        return new_options


def migrate_label_max_and_show_price_merge(hass, entry, options, name):
    """Migrate old boolean 'label_max' and 'label_minmax_show_price' to new dropdown.

    This function handles the migration of label_max from boolean to dropdown format,
    incorporating the label_minmax_show_price option:

    - label_max=False → label_max="off"
    - label_max=True + label_minmax_show_price=False → label_max="on_no_price"
    - label_max=True + label_minmax_show_price=True → label_max="on"

    The migration is performed when label_max is a boolean value. Options not explicitly
    set use their old default values (label_max=True, label_minmax_show_price=True).
    After migration, the label_minmax_show_price option remains for label_min migration.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    value_map = {
        (False, True): LABEL_MAX_OFF,
        (False, False): LABEL_MAX_OFF,
        (True, False): LABEL_MAX_ON_NO_PRICE,
        (True, True): LABEL_MAX_ON,
    }
    return _migrate_boolean_with_secondary_to_dropdown(
        hass, entry, options, name,
        CONF_LABEL_MAX, "label_minmax_show_price",
        True, True, value_map, remove_secondary=False
    )


def migrate_label_min_and_show_price_merge(hass, entry, options, name):
    """Migrate old boolean 'label_min' and 'label_minmax_show_price' to new dropdown.

    This function handles the migration of label_min from boolean to dropdown format,
    incorporating the label_minmax_show_price option:

    - label_min=False → label_min="off"
    - label_min=True + label_minmax_show_price=False → label_min="on_no_price"
    - label_min=True + label_minmax_show_price=True → label_min="on"

    The migration is performed when label_min is a boolean value. Options not explicitly
    set use their old default values (label_min=True, label_minmax_show_price=True).
    After migration, the label_minmax_show_price option is removed.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    value_map = {
        (False, True): LABEL_MIN_OFF,
        (False, False): LABEL_MIN_OFF,
        (True, False): LABEL_MIN_ON_NO_PRICE,
        (True, True): LABEL_MIN_ON,
    }
    return _migrate_boolean_with_secondary_to_dropdown(
        hass, entry, options, name,
        CONF_LABEL_MIN, "label_minmax_show_price",
        True, True, value_map, remove_secondary=True
    )


def migrate_show_y_axis_and_tick_marks_merge(hass, entry, options, name):
    """Migrate old boolean 'show_y_axis' and 'show_y_axis_tick_marks' to new dropdown.

    This function handles the migration of show_y_axis from boolean to dropdown format,
    incorporating the show_y_axis_tick_marks option:

    - show_y_axis=False → show_y_axis="off"
    - show_y_axis=True + show_y_axis_tick_marks=False → show_y_axis="on"
    - show_y_axis=True + show_y_axis_tick_marks=True → show_y_axis="on_with_tick_marks"

    The migration is performed when show_y_axis is a boolean value. Options not explicitly
    set use their old default values (show_y_axis=True, show_y_axis_tick_marks=False).
    After migration, the show_y_axis_tick_marks option is removed.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    value_map = {
        (False, True): SHOW_Y_AXIS_OFF,
        (False, False): SHOW_Y_AXIS_OFF,
        (True, False): SHOW_Y_AXIS_ON,
        (True, True): SHOW_Y_AXIS_ON_WITH_TICK_MARKS,
    }
    return _migrate_boolean_with_secondary_to_dropdown(
        hass, entry, options, name,
        CONF_SHOW_Y_AXIS, CONF_SHOW_Y_AXIS_TICK_MARKS,
        True, False, value_map, remove_secondary=True
    )


def migrate_cheap_periods_on_x_axis_merge(hass, entry, options, name):
    """Migrate old 'cheap_price_on_x_axis' and 'cheap_labels_in_separate_row' to new dropdown.

    This function handles the migration of cheap_price_on_x_axis from boolean to dropdown format,
    incorporating the cheap_labels_in_separate_row option:

    - cheap_price_on_x_axis=False → cheap_periods_on_x_axis="off"
    - cheap_price_on_x_axis=True + cheap_labels_in_separate_row=True → cheap_periods_on_x_axis="on_comfy"
    - cheap_price_on_x_axis=True + cheap_labels_in_separate_row=False → cheap_periods_on_x_axis="on_compact"

    The migration is performed when cheap_price_on_x_axis is a boolean value. Options not explicitly
    set use their old default values (cheap_price_on_x_axis=False, cheap_labels_in_separate_row=True).
    After migration, both old options are removed.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    value_map = {
        (False, True): CHEAP_PERIODS_ON_X_AXIS_OFF,
        (False, False): CHEAP_PERIODS_ON_X_AXIS_OFF,
        (True, True): CHEAP_PERIODS_ON_X_AXIS_ON_COMFY,
        (True, False): CHEAP_PERIODS_ON_X_AXIS_ON_COMPACT,
    }
    return _migrate_boolean_with_secondary_to_dropdown(
        hass, entry, options, name,
        CONF_CHEAP_PRICE_ON_X_AXIS, CONF_CHEAP_LABELS_IN_SEPARATE_ROW,
        False, True, value_map,
        new_primary_key=CONF_CHEAP_PERIODS_ON_X_AXIS, remove_secondary=True
    )


def migrate_refresh_mode_option(hass, entry, options, name):
    """Migrate old 'auto_refresh_enabled' boolean option to new 'refresh_mode' dropdown.

    This function converts the deprecated boolean option to the new dropdown format:
    - auto_refresh_enabled=False → refresh_mode="system"
    - auto_refresh_enabled=True → refresh_mode="system_interval"

    The migration is performed only once when the old option exists.
    After migration, the old option is removed from the config entry.

    Args:
        hass: Home Assistant instance
        entry: Config entry to migrate
        options: Current options dictionary
        name: Entity name for logging

    Returns:
        dict: Updated options dictionary if migration occurred, otherwise original options
    """
    return _migrate_boolean_to_dropdown(
        hass, entry, options, name,
        CONF_AUTO_REFRESH_ENABLED, CONF_REFRESH_MODE,
        REFRESH_MODE_SYSTEM_INTERVAL, REFRESH_MODE_SYSTEM
    )


def migrate_entity_unique_id(hass, entry, name, entity_type, old_suffix, new_suffix):
    """Rename entity with old unique_id suffix to new naming standard.

    This migration updates the unique_id of entities that were created with old
    naming conventions. The new unique_id uses the updated suffix while preserving
    the entity's history.

    Args:
        hass: Home Assistant instance
        entry: Config entry to check
        name: Entity name for logging
        entity_type: Entity type ("camera", "image", or "sensor")
        old_suffix: Old suffix used in unique_id (e.g., "", "_last_update")
        new_suffix: New suffix to use in unique_id (e.g., "_camera", "_status")
    """
    if not entry:
        return

    from homeassistant.helpers import entity_registry as er

    entity_registry = er.async_get(hass)

    # Generate what the old and new unique_id would be
    name_sanitized = name.lower().replace(" ", "_").replace("-", "_")
    unique_suffix = entry.entry_id.split("-")[0]

    if old_suffix:
        old_unique_id = f"{entity_type}_tibber_graph_{name_sanitized}_{old_suffix}_{unique_suffix}"
    else:
        old_unique_id = f"{entity_type}_tibber_graph_{name_sanitized}_{unique_suffix}"

    new_unique_id = f"{entity_type}_tibber_graph_{name_sanitized}_{new_suffix}_{unique_suffix}"

    # Check if the old entity exists
    old_entity_entry = entity_registry.async_get_entity_id(entity_type, "tibber_graph", old_unique_id)

    if old_entity_entry:
        # Check if new unique_id already exists (to avoid conflicts)
        new_entity_exists = entity_registry.async_get_entity_id(entity_type, "tibber_graph", new_unique_id)

        if new_entity_exists:
            _LOGGER.warning(
                "Cannot migrate %s entity %s: new unique_id %s already exists. "
                "Please remove one of the entities manually.",
                entity_type, old_entity_entry, new_unique_id
            )
            return

        _LOGGER.info(
            "Migrating '%s' entity '%s': updating unique_id from '%s' to '%s' for '%s'",
            entity_type, old_entity_entry, old_unique_id, new_unique_id, name
        )

        # Update the unique_id to the new format
        entity_registry.async_update_entity(
            old_entity_entry,
            new_unique_id=new_unique_id
        )

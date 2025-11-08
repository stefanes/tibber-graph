"""Migration utilities for Tibber Graph configuration options.

This module contains functions to migrate deprecated configuration options
to their new equivalents, ensuring backward compatibility across versions.
"""
import logging

from .const import (
    CONF_START_GRAPH_AT,
    CONF_THEME,
    CONF_TRANSPARENT_BACKGROUND,
    CONF_LABEL_CURRENT_IN_HEADER,
    CONF_SHOW_X_AXIS_TICK_MARKS,
    CONF_SHOW_Y_AXIS_TICK_MARKS,
    START_GRAPH_AT_MIDNIGHT,
    START_GRAPH_AT_CURRENT_HOUR,
)

_LOGGER = logging.getLogger(__name__)


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
    if not entry:
        return options

    # Check if old option exists in either options or data
    old_key = "start_at_midnight"
    has_old_option = False
    old_value = None

    # Check options first (priority)
    if options and old_key in options:
        has_old_option = True
        old_value = options[old_key]
        location = "options"
    # Then check entry.data
    elif old_key in entry.data:
        has_old_option = True
        old_value = entry.data[old_key]
        location = "data"

    # Only migrate if old option exists and new option doesn't
    if has_old_option and CONF_START_GRAPH_AT not in (options or {}):
        # Convert boolean to new dropdown value
        new_value = START_GRAPH_AT_MIDNIGHT if old_value else START_GRAPH_AT_CURRENT_HOUR

        _LOGGER.info(
            "Migrating %s option for %s: start_at_midnight=%s → start_graph_at=%s",
            location, name, old_value, new_value
        )

        # Update the config entry with new option and remove old one
        new_options = dict(options) if options else {}
        new_options[CONF_START_GRAPH_AT] = new_value

        # Remove old option from the dict we're updating
        if old_key in new_options:
            del new_options[old_key]

        # Update the config entry
        hass.config_entries.async_update_entry(
            entry,
            options=new_options
        )

        return new_options

    return options


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
            "Migrating %s for %s: theme='dark_black' → theme='dark' + transparent_background=True",
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
    if not entry:
        return options

    # Check if old option exists in either options or data
    old_key = "label_current_at_top"
    has_old_option = False
    old_value = None

    # Check options first (priority)
    if options and old_key in options:
        has_old_option = True
        old_value = options[old_key]
        location = "options"
    # Then check entry.data
    elif old_key in entry.data:
        has_old_option = True
        old_value = entry.data[old_key]
        location = "data"

    # Only migrate if old option exists and new option doesn't
    if has_old_option and CONF_LABEL_CURRENT_IN_HEADER not in (options or {}):
        _LOGGER.info(
            "Migrating %s option for %s: label_current_at_top=%s → label_current_in_header=%s",
            location, name, old_value, old_value
        )

        # Update the config entry with new option and remove old one
        new_options = dict(options) if options else {}
        new_options[CONF_LABEL_CURRENT_IN_HEADER] = old_value

        # Remove old option from the dict we're updating
        if old_key in new_options:
            del new_options[old_key]

        # Update the config entry
        hass.config_entries.async_update_entry(
            entry,
            options=new_options
        )

        return new_options

    return options


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

    # Check if old option exists in either options or data
    has_old_option = False
    old_value = None

    # Check options first (priority)
    if options and old_key in options:
        has_old_option = True
        old_value = options[old_key]
        location = "options"
    # Then check entry.data
    elif old_key in entry.data:
        has_old_option = True
        old_value = entry.data[old_key]
        location = "data"

    # Only migrate if old option exists and new option doesn't
    if has_old_option and new_key not in (options or {}):
        _LOGGER.info(
            "Migrating %s option for %s: %s=%s → %s=%s",
            location, name, old_key, old_value, new_key, old_value
        )

        # Update the config entry with new option and remove old one
        new_options = dict(options) if options else {}
        new_options[new_key] = old_value

        # Remove old option from the dict we're updating
        if old_key in new_options:
            del new_options[old_key]

        # Update the config entry
        hass.config_entries.async_update_entry(
            entry,
            options=new_options
        )

        return new_options

    return options


def migrate_show_x_ticks_option(hass, entry, options, name):
    """Migrate old 'show_x_ticks' option to new 'show_x_axis_tick_marks'.

    This function renames the option from the old name to the new name:
    - show_x_ticks → show_x_axis_tick_marks

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
        "show_x_ticks", CONF_SHOW_X_AXIS_TICK_MARKS
    )


def migrate_show_y_axis_ticks_option(hass, entry, options, name):
    """Migrate old 'show_y_axis_ticks' option to new 'show_y_axis_tick_marks'.

    This function renames the option from the old name to the new name:
    - show_y_axis_ticks → show_y_axis_tick_marks

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
        "show_y_axis_ticks", CONF_SHOW_Y_AXIS_TICK_MARKS
    )

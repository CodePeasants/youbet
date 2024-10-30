# Unreleased

# 0.2.1 - 2024-10-29
## Fixed
- No longer produce internal server error when a user has a wager in a completed round and tries to access a round where they do not have a wager.

# 0.2.0 - 2024-10-20
**Note:** This version modifies the database tables and will require rebuilding the database.

## Added
- Changelog.
- Default round name to "Round #" with an incrementing number
- Default starting money for events is not configurable with the `DEFAULT_STARTING_MONEY` variable in settings.py. If not configured, will default to 100.
- Added settings to Event's
    - Toggle to disallow insider betting to prevent users from betting on matches they are playing in.
    - Configurable maximum number of participants for events.
- Added option on round page to delete the round.
- Added wager editor interface to the round page to allow users to create new wagers from that page.

## Changed
- Space optimization for mobile:
    - Replaced status column of rounds table on event page with a status badge in front of the name of the event.
    - Moved breadcrumbs out of the nav bar to prevent running out of space.
- Removed in-line edit and delete buttons from tables to prevent misclicks on mobile.
- Increased the brightness of the Bootstrap `suxxess` class color.
- Disabled wager editor in rounds table on event page to save space on mobile.

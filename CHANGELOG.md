# Unreleased

# 0.4.0 - 2024-10-30
## Added
- Permissions security for access attempts to unauthorized routes.

## Fixed
- Join event button no longer displays when the event is not joinable.
- Users who have not refreshed pages that include editors that post to routes that should no longer be available will now get a warning message instead of allowing the post.

# 0.3.0 - 2024-10-29
**Note:** This version modifies the database tables and will require rebuilding the database.

## Added
- A new `Competitor` table and associated controlls to make non-player competitors. This is useful if players in the event are betting on matches
between competitors that are not participating in betting. E.g. if betting on a sporting event between third parties.
- An option on `Event`'s to decide if the participating players are also considered competitors or not.

## Changed
- `User` table now inherits from a `CompetitorBase` table along with the new `Competitor` table using joined-table inheritance. So they can be used interchangeably where needed.

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

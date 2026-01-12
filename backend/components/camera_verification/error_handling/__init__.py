'''
# Error Handling
Catches and processes exceptions raised during worker verification and turns them into human-readable responses for REST API, as well as for entry event logging. Handles **not only** error states, but normal state as well, that is no exception.

## Directory Structure

#### `errorConfig.py`
- Contains configurations for Exception processing, defining Response format and mappings of exceptions to messages.

#### `errorService.py`
- Contains logic and functions for processing exceptions into Responses defined in errorConfig.

'''

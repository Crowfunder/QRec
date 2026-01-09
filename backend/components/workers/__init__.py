'''
# Workers


The `workers` module manages all worker-related operations, including CRUD functionality, onboarding, and entry pass generation. It serves as the central component for handling worker data and interactions.



## Components

#### `workerController.py`
- Defines API endpoints for worker-related operations.
- Handles HTTP requests and responses for:
  - Creating, reading, updating, and deleting worker records.
  - Generating worker entry passes (e.g., QR codes).

#### `workerService.py`
- Implements the business logic for worker management.
- Provides functionality for:
  - Worker onboarding and data validation.
  - Generating and managing worker-specific data (e.g., face embeddings, QR codes).
  - Interfacing with the database to perform CRUD operations.

'''
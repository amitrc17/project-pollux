# Project Pollux

A personal asset management system that organizes and categorizes your possessions using an intelligent tree-based structure with LLM-powered categorization.

## Overview

Project Pollux is a web application designed to help users track and organize their possessions through a dynamic, hierarchical categorization system called "Asset Forests." The system allows users to upload images of their items, create custom categories (descriptors), and visualize their possessions in an organized tree structure.

### Key Concepts

**Asset Forest**: A representation of a user's possessions organized as a forest of trees. Each forest belongs to one user, with each tree rooted at a high-level category.

**Node Types**:
- **User**: Root nodes of the forest, representing the owner
- **Descriptor**: Internal nodes representing categories (e.g., "Indoor Appliance", "Kitchen Tools")
  - Can describe location, usage, physical attributes, or any categorical information
  - Dynamically created and tailored to each user
  - Can be leaf nodes (indicating no assets in that category yet)
- **Asset**: Leaf nodes representing actual possessions
  - Created from user inputs (images, text, etc.)
  - Always terminal nodes in the tree structure
- **Image**: Binary data attached to assets, stored separately for efficiency

## Technology Stack

### Backend
- **Python 3** with Flask web framework
- **Redis** - Primary database for user credentials and asset trees
- **SQLite** - Storage for image binary data
- **LangChain + OpenAI** - LLM integration for intelligent categorization
- **Pyre** - Static type checking

### Frontend
- **React 18** - UI framework
- **ReactFlow (@xyflow/react)** - Interactive tree visualization
- **Axios** - HTTP client for API communication

## Prerequisites

- Python 3.x with pip
- Node.js and npm/yarn
- Redis server
- OpenAI API key (for LLM features)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/amitrc17/project-pollux.git
   cd project-pollux
   ```

2. **Set up Python environment** (optional but recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install flask flask-cors redis langchain langchain-openai markupsafe
   ```

4. **Install Node.js dependencies**
   ```bash
   cd webapp/web
   npm install
   cd ../..
   ```

5. **Configure environment variables**
   - Set your OpenAI API key and other LLM configuration in `webapp/web/llm/llm_engine.py`

## Running the Application

You'll need **three terminal windows** to run the complete application:

### Terminal 1: Redis Server
```bash
cd project-pollux
redis-server
```
This starts Redis on port 6379 and creates a `redis.rdb` file for data persistence.

### Terminal 2: Flask Backend
```bash
cd project-pollux/webapp/web
yarn start-api
# or: npm run start-api
```
This starts the Flask API server on port 5000.

### Terminal 3: React Frontend
```bash
cd project-pollux/webapp/web
npm start
```
This starts the React development server on port 3000.

### Access the Application
Open your browser and navigate to `http://localhost:3000`

## Project Structure

```
project-pollux/
├── README.md
├── webapp/
│   ├── app.py                    # Flask application with API endpoints
│   ├── pollux.py                 # Test utilities and examples
│   └── web/
│       ├── data/                 # Core data models and database
│       │   ├── node.py          # Base Node class
│       │   ├── pid.py           # Unique identifier system
│       │   ├── database.py      # Redis and SQLite abstractions
│       │   ├── asset_tree.py    # Asset tree utilities
│       │   ├── nodes/           # Node type implementations
│       │   │   ├── user.py
│       │   │   ├── descriptor.py
│       │   │   ├── asset.py
│       │   │   └── image.py
│       │   └── factories/       # Factory pattern for node creation
│       │       └── node_factory.py
│       ├── llm/                 # LLM integration
│       │   └── llm_engine.py    # OpenAI integration for categorization
│       ├── mutators/            # Tree manipulation operations
│       │   ├── mutator.py       # Abstract base class
│       │   ├── explode.py       # Split descriptors into granular ones
│       │   ├── coalesce.py      # Merge similar descriptors
│       │   ├── dedupe.py        # Remove duplicate nodes
│       │   └── delete.py        # Node deletion
│       ├── image_processing/    # Image handling utilities
│       │   └── image_processor.py
│       └── src/                 # React frontend
│           ├── App.js           # Main React component
│           └── ...
```

## Core Components

### Database Layer
- **NodeDB**: Redis-based storage for asset trees and nodes
  - Fast read/write for small objects
  - Stores serialized node data
- **UserDB**: Redis-based user credential storage
  - Hash-based authentication
  - Maps username+password hash to user ID
- **ImageStore**: SQLite-based binary storage for images
  - Efficient blob storage
  - Referenced by image handles in Redis

### Node System
All entities inherit from the abstract `Node` class:
- **Unique IDs (PID)**: Each node has a unique identifier
- **Edges**: Directed connections to other nodes (stored as PID lists)
- **Serialization**: Nodes can be serialized to JSON for database storage
- **Factory Pattern**: NodeFactory handles creation and deserialization

### Mutator Interface
A standardized system for manipulating asset trees:
- **Mutator Base Class**: Abstract interface for tree operations
- **AssetTree**: Utility class for tree traversal and filtering
- **MutatorResult**: Standardized result objects
- **Example Mutators**: Validation, node splitting, deduplication, merging

See `webapp/web/mutators/README.md` for detailed documentation.

### LLM Integration
OpenAI-powered features for intelligent categorization:
- **Image Description**: Extract objects from uploaded images
- **Bucket Finding**: Suggest appropriate categories for assets
- **Bucket Suggestion**: Generate new category names
- **Sub-bucket Detection**: Identify hierarchical category relationships
- **Bucket Expansion**: Split broad categories into granular ones
- **Bucket Merging**: Combine related categories

## API Endpoints

### `GET /message`
Health check endpoint
- **Response**: `{"message": "Have fun"}`

### `POST /login`
User authentication
- **Body**: `{"username": string, "password": string}`
- **Response**: `{"success": "yes"|"no", ...user_data}`

### `POST /register`
User registration (attempts login first)
- **Body**: `{"username": string, "password": string}`
- **Response**: `{"success": "yes"|"no", "existence": "yes"|"no", ...user_data}`

### `POST /upload`
Upload an image and attach it to a user
- **Body (form-data)**: 
  - `userid`: User's PID
  - `image`: Image file
- **Response**: `{"success": "yes"|"no", ...image_data}`

### `POST /add_descriptor`
Create a new descriptor for a user
- **Body (form-data)**:
  - `userid`: User's PID
  - `descriptor_name`: Name of the category
- **Response**: `{"success": "yes"|"no", "userid": string, "descriptorid": string}`

### `POST /get_asset_tree`
Retrieve the complete asset tree for visualization
- **Body**: `{"userid": string}`
- **Response**: `{"success": "yes"|"no", "nodes_info": [...]}`

## Features

### Current Features
- ✅ User registration and authentication
- ✅ Image upload and storage
- ✅ Dynamic descriptor (category) creation
- ✅ Asset tree visualization with ReactFlow
- ✅ Hierarchical organization of possessions
- ✅ Redis-based persistent storage
- ✅ LLM-powered image description
- ✅ Intelligent category suggestion

### Tree Manipulation (Mutators)
- ✅ Node validation
- ✅ Node explosion (split multi-concept descriptors)
- ✅ Node coalescing (merge similar categories)
- ✅ Deduplication
- ✅ Tree cleanup operations

## Development Workflow

### Testing
Run the test utilities in `webapp/pollux.py`:
```bash
cd project-pollux
python -m webapp.pollux
```

### Type Checking
The project uses Pyre for static type checking:
```bash
pyre check
```

### Frontend Development
React hot-reload is enabled by default:
```bash
cd webapp/web
npm start
```
Changes to React components will automatically reload in the browser.

### Backend Development
For Flask development with auto-reload:
```bash
cd webapp/web
FLASK_ENV=development yarn start-api
```

## Data Model

### Node Relationships
- Users → Descriptors (one-to-many)
- Descriptors → Descriptors (many-to-many, creating hierarchies)
- Descriptors → Assets (one-to-many)
- Assets → Images (one-to-many)

### Edge Semantics
- Edges are **directed** and **not bidirectional**
- If Node A has an edge to Node B, B does not automatically have an edge to A
- This design simplifies edge management but requires careful handling

### Serialization Format
Nodes are serialized to JSON strings for storage:
```json
{
  "id": "User:1234567890",
  "name": "username",
  "edges": ["Descriptor:9876543210"],
  "created_at": 1234567890.123,
  "updated_at": 1234567890.123
}
```

## Contributing

When adding new features:
1. Follow the existing Node/Factory patterns
2. Create mutators for tree operations (don't modify nodes directly)
3. Add proper type hints (Pyre-compatible)
4. Update database models when adding new node types
5. Document new API endpoints in this README

## License

[Add license information]

## Contact

[Add contact/maintainer information]

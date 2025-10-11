# Mutator Interface Documentation

This directory contains the generic mutator interface for manipulating Asset Trees and Nodes in the Pollux system.

## Overview

The mutator interface provides a standardized way to create operations that can work on:
1. **Complete Asset Trees** - For tree-wide operations like validation, reorganization, or global optimizations
2. **Specific sets of nodes** - For targeted operations on filtered subsets
3. **Individual nodes** - For single-node operations

## Core Components

### Mutator (Abstract Base Class)
The main abstract class that all mutators must inherit from. It provides:
- `execute_on_tree(asset_tree: AssetTree)` - Process an entire asset tree
- `execute_on_nodes(nodes: List[Node])` - Process a specific set of nodes  
- `execute_on_node(node: Node)` - Process a single node (default implementation)
- Node type validation and filtering utilities
- Logging capabilities

### AssetTree
A utility class that represents a user's asset forest and provides methods for:
- Tree traversal (BFS, getting nodes by type, depth calculation)
- Filtering nodes by type (Assets, Descriptors, Users)
- Finding leaf nodes
- Caching nodes for performance

### MutatorResult
A standardized result object that contains:
- Success status and message
- Lists of modified, created, and deleted nodes
- Metadata for additional operation details

### CompositeMutator
A mutator that executes multiple mutators in sequence, useful for creating complex workflows.

## Usage Examples

### Creating a Custom Mutator

```python
from typing import List
from pyre_extensions import override
from .mutator import Mutator, MutatorResult, AssetTree
from ..data.node import Node

class MyCustomMutator(Mutator):
    def __init__(self):
        super().__init__("MyCustomMutator")
    
    @override
    def execute_on_tree(self, asset_tree: AssetTree) -> MutatorResult:
        # Process entire tree
        all_nodes = asset_tree.get_all_nodes()
        # ... your logic here
        return MutatorResult(success=True, message="Tree processed")
    
    @override
    def execute_on_nodes(self, nodes: List[Node]) -> MutatorResult:
        # Process specific nodes
        # ... your logic here
        return MutatorResult(success=True, message=f"Processed {len(nodes)} nodes")
```

### Using a Mutator

```python
from ..data.nodes.user import User
from .mutator import AssetTree
from .example_mutators import ValidationMutator

# Create an asset tree from a user
user = User.from_id(user_id, factory)
asset_tree = AssetTree(user)

# Create and run a mutator
validation_mutator = ValidationMutator()
result = validation_mutator.execute_on_tree(asset_tree)

if result.success:
    print(f"Validation passed: {result.message}")
else:
    print(f"Validation failed: {result.message}")
    print(f"Issues found: {result.metadata.get('validation_issues', [])}")
```

### Creating Composite Workflows

```python
from .mutator import CompositeMutator
from .example_mutators import ValidationMutator, NodeExplodeMutator

# Create a workflow that validates, then explodes nodes
workflow = CompositeMutator("ValidationAndExplosion", [
    ValidationMutator(),
    NodeExplodeMutator()
])

result = workflow.execute_on_tree(asset_tree)
```

## Available Example Mutators

### ValidationMutator
Validates the integrity of Asset Trees and node relationships:
- Checks for broken edges and orphaned nodes
- Validates that Assets are leaf nodes
- Detects cycles in the tree structure
- Validates node properties (names, timestamps, etc.)

### NodeExplodeMutator  
Splits descriptor nodes into more granular descriptors:
- Identifies descriptors that contain multiple concepts
- Creates new descriptors for each concept
- Example: "Kitchen and Dining" → "Kitchen", "Dining"

## Mutator Design Guidelines

1. **Inherit from Mutator**: All mutators should extend the abstract `Mutator` class
2. **Implement required methods**: Both `execute_on_tree` and `execute_on_nodes` are required
3. **Return MutatorResult**: Always return a properly constructed `MutatorResult` object
4. **Use logging**: Call `self.log_operation()` to log important operations
5. **Validate inputs**: Override `validate_nodes()` and `get_supported_node_types()` as needed
6. **Handle errors gracefully**: Return failed MutatorResult objects instead of throwing exceptions
7. **Be atomic**: Mutators should either complete fully or fail cleanly without partial state

This interface provides a flexible foundation for building mutators like:
- **Deduplication mutators** (remove similar nodes)
- **Reorganization mutators** (restructure tree hierarchy) 
- **ML-powered mutators** (automatic categorization, similarity detection)
- **Import/export mutators** (data migration operations)
- **Cleanup mutators** (remove orphaned nodes, fix inconsistencies)

The design follows the Asset Tree structure described in your README, respecting the constraints that Users are roots, Descriptors are internal nodes, and Assets are leaves.

## Node Type Constraints

Based on the Asset Tree structure:
- **User**: Root nodes of trees, can connect to Descriptors
- **Descriptor**: Internal nodes, can connect to other Descriptors, Assets, or Users
- **Asset**: Leaf nodes, should not have outgoing edges

Mutators should respect these constraints when creating or modifying nodes.

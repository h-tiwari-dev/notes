---
title: Consistency in Distributed Systems
tags: models, replication, architecture, distributed-systems, theorem, consistency, cap-theorem, systems
aliases:
  - Distributed Consistency
  - Data Consistency
created:
  "{ date }": 
last_modified:
  "{ date }": 
author: Your Name
status: Complete
type: Technical Documentation
related:
  - CAP Theorem
  - Distributed Systems
  - Data Replication
  - System Architecture
cssclasses:
  - technical-doc
---
# Consistency in Distributed Systems

A measure of how up to date the data is in a distributed system. In distributed systems, consistency refers to how data remains synchronized across multiple nodes or replicas.

## Data Consistency Levels

### 1. Linearizable Consistency
- Most strict consistency level
- Shows all changes in database until current read request
- All changes before read operation are reflected in read query
- Uses single-threaded single server
- Every read and write request strictly ordered

Example:
```mermaid
sequenceDiagram
    participant Client
    participant Server
    
    Note over Client,Server: Initial x = 10
    Client->>Server: update x to 13
    Client->>Server: update x to 17
    Client->>Server: read x
    Server-->>Client: Returns 17
    Client->>Server: update x to 1
    Client->>Server: read x
    Server-->>Client: Returns 1
```

### 2. Eventual Consistency
- Can send stale data for read requests
- Eventually returns latest data (if data isn't updated)
- System becomes consistent after some time
- Can process read and write requests parallelly using multiple servers

Example:
```mermaid
sequenceDiagram
    participant Client
    participant Server1
    participant Server2
    
    Note over Client,Server2: Write before read, but read processed first
    Client->>Server1: Write x = 10
    Client->>Server2: Read x
    Server2-->>Client: Returns x = 5 (stale)
    Note over Client,Server2: Eventually consistent
    Client->>Server2: Read x (later)
    Server2-->>Client: Returns x = 10
```

### 3. Causal Consistency
- Orders operations based on dependencies
- Previous related operations must execute first
- Independent operations can execute in any order

Example:
```mermaid
graph LR
    A[update x = 20] --> B[read x]
    B --> C[update x = 2]
    D[update y = 10] --> E[read y]
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#f9f,stroke:#333
```
#### Limitations with Aggregation Operations

Causal Consistency fails when performing aggregation operations due to its ID-based ordering nature versus aggregation's need to work across all IDs.

Example Table:
```mermaid
graph TD
    subgraph Initial_Table
    A["UID: Value"]
    B["1: 20"]
    C["2: 10"]
    D["3: 30"]
    end
```

Consider these operations:
1. read sum
2. update 1 to 10
3. read sum
4. update 1 to 5

```mermaid
graph TD
    subgraph Failed Execution Patterns
    A[Pattern 1: Sum ops together, <br>updates after] --> B[Result: 60, 60<br>Wrong]
    C[Pattern 2: Sum ops together, <br>updates before] --> D[Result: 45, 45<br>Wrong]
    E[Pattern 3: First update, <br>then sums] --> F[Result: 60, 60<br>Wrong]
    end
    
    style A fill:#f96,stroke:#333
    style C fill:#f96,stroke:#333
    style E fill:#f96,stroke:#333
```

**Why It Fails:**
- Causal consistency orders queries based on individual IDs
- Aggregation operations (like SUM) need to work across all IDs simultaneously
- No permutation of operations can guarantee correct results
- This creates a fundamental conflict between causal ordering and aggregate operations

```mermaid
graph LR
    A[Causal Consistency] --> B[Orders by ID]
    C[Aggregation Operations] --> D[Needs All IDs]
    B --> E[Conflict]
    D --> E
    
    style E fill:#f96,stroke:#333
```

**Example Breakdown:**
```mermaid
sequenceDiagram
    participant DB as Database
    participant Op as Operations
    
    Note over DB,Op: Initial Sum = 60 (20+10+30)
    Op->>DB: Update ID 1: 20->10
    Note over DB,Op: Should be 50 (10+10+30)
    Op->>DB: Update ID 1: 10->5
    Note over DB,Op: Should be 45 (5+10+30)
    Note over DB,Op: But results are inconsistent
```

This limitation shows that while causal consistency is effective for operations on individual keys, it's not suitable for operations that need to maintain consistency across multiple keys simultaneously.

-----

### 4. Quorum Consistency
- Multiple replicas may not be in sync
- Read queries fetch from all replicas
- Returns most appropriate values
- Eventually consistent in most cases

```mermaid
graph TD
    Q[Quorum System] --> R1[Replica 1: x=20]
    Q --> R2[Replica 2: x=40]
    Q --> R3[Replica 3: x=20]
    
    style Q fill:#f96,stroke:#333
```


### Trade-off Formula for Quorum:

- R + W > N: Strong consistency
- R + W ≤ N: Eventual consistency Where:
- R = Read replicas
- W = Write replicas
- N = Total replicas

```mermaid
graph TD
    subgraph "Quorum Configuration"
        Q["Quorum System"]
        Q --> SC["Strong Consistency<br>R + W > N"]
        Q --> EC["Eventual Consistency<br>R + W ≤ N"]
    end

    style Q fill:#f96,stroke:#333
    style SC fill:#bbf,stroke:#333
    style EC fill:#f9f,stroke:#333
```

## Consistency Level Comparison

### Comparison Table

| Level | Consistency | Efficiency |
|-------|-------------|------------|
| Linearizable | Highest | Lowest |
| Eventual Consistency | Lowest | Highest |
| Causal Consistency | Higher than Eventual,<br>Lower than Linearizable | Higher than Linearizable,<br>Lower than Eventual |
| Quorum | Configurable | Configurable |

```mermaid
graph LR
    subgraph "Consistency Scale"
        direction LR
        L1["Linearizable"] --> C1["Causal"] --> E1["Eventual"]
    end
    
    subgraph "Efficiency Scale"
        direction LR
        E2["Eventual"] --> C2["Causal"] --> L2["Linearizable"]
    end

    style L1 fill:#f96,stroke:#333
    style L2 fill:#f96,stroke:#333
    style E1 fill:#bbf,stroke:#333
    style E2 fill:#bbf,stroke:#333
    style C1 fill:#f9f,stroke:#333
    style C2 fill:#f9f,stroke:#333
```


## Transaction Isolation Levels

### Efficiency vs Isolation Trade-off
```mermaid
graph LR
    A[Efficiency] --> B[Read Uncommitted]
    B --> C[Read Committed]
    C --> D[Repeatable Read]
    D --> E[Serializable]
    
    style A fill:#f96,stroke:#333
```

1. Read Uncommitted
   - Overwritten on update operations
   - Lowest isolation, highest efficiency

2. Read Committed
   - Local copy of changed values
   - Old value in DB, new in local copy until commit

3. Repeatable Read
   - Versioning of unchanged values
   - Stores all historical values for keys

4. Serializable
   - Uses queued locks
   - Causal ordering
   - Highest isolation, lowest efficiency

## Implementation Techniques

### Two-Phase Commit (2PC)
```mermaid
sequenceDiagram
    participant C as Coordinator
    participant N1 as Node1
    participant N2 as Node2
    
    Note over C,N2: Phase 1 - Prepare
    C->>N1: Prepare
    C->>N2: Prepare
    N1-->>C: Ready
    N2-->>C: Ready
    Note over C,N2: Phase 2 - Commit
    C->>N1: Commit
    C->>N2: Commit
```

### Quorum-based Implementation
```mermaid
graph TD
    W[Write Quorum] --> N1[Node 1]
    W --> N2[Node 2]
    W --> N3[Node 3]
    R[Read Quorum] --> N1
    R --> N2
    
    style W fill:#f96,stroke:#333
    style R fill:#bbf,stroke:#333
```

## CAP Theorem Trade-offs
```mermaid
graph TD
    CAP[CAP Theorem] --> C[Consistency]
    CAP --> A[Availability]
    CAP --> P[Partition Tolerance]
    
    style CAP fill:#f96,stroke:#333
```

1. CP Systems
   - Banking systems
   - Financial transactions

2. AP Systems
   - Social media
   - Content delivery

## Best Practices

1. Monitoring Metrics
```mermaid
graph TD
    M[Monitoring] --> RL[Replication Lag]
    M --> CR[Conflict Rate]
    M --> RT[Resolution Time]
    M --> SS[Sync Status]
```

1. Conflict Resolution Strategies
```mermaid
graph LR
    C[Conflict] --> LWW[Last-Write-Wins]
    C --> VC[Vector Clocks]
    C --> CRDT[CRDTs]
```

## Performance Considerations

For optimal performance, consider:
1. Read vs Write ratio
2. Consistency requirements
3. Latency tolerance
4. Network partition frequency

#distributed-systems #consistency #cap-theorem #replication

## Suggested Related Documents
[[CAP Theorem.md]]\|"CAP Theorem Consistency Relationship"

This link text effectively connects the two documents by highlighting their shared focus on consistency within the context of the CAP theorem in distributed systems.]]
[[Distributed Consistency with Paxos Protocol.md]]\|"Paxos Consistency Implementation"

This link text effectively connects the general concept of consistency in distributed systems (source) to its specific implementation through the Paxos protocol (target).]]
[[Consistent Hashing.md]]\|"Distributed System Hashing Concepts"

This link text effectively connects the two documents by:
1. Acknowledging the distributed systems context they share
2. Referencing the hashing focus of the target document
3. Keeping it general enough to bridge consistency and hashing concepts]]

## Backlinks
- [[Distributed Consistency with Paxos Protocol.md]]\|"Paxos Consensus Implementation Details"

This link text effectively connects the source document about the Paxos protocol to the broader topic of consistency in distributed systems, highlighting that Paxos is a specific implementation method for achieving distributed consistency.]]
- [[CAP Theorem.md]]\|"CAP Theorem Consistency Principles"

This link text effectively connects the documents by:
1. Referencing the main topic of the source (CAP Theorem)
2. Highlighting the target's focus (Consistency)
3. Indicating the theoretical nature of both documents (Principles)]]
- [[Consistent Hashing.md]]\|"Distributed System Consistency Patterns"

This link text connects the two documents by highlighting how consistent hashing is one of the key patterns used to achieve consistency in distributed systems, bridging the technical relationship between these related concepts.]]

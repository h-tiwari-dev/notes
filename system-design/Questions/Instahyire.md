#backend-development #system-scalability #fullstack-engineering #fintech #fullstack-development #fintech-development #api-architecture #system-scaling #backend-engineering

#backend-development #fintech #fullstack-engineering #system-scalability

Experience & Compensation
Q: Please state your Total experience, CTC, ECTC, and Notice period. (If holding an offer, please mention that as well) REQUIRED  
A:

- Total Experience: 3.6+ years
- Current CTC & ECTC: 20 LPA → 26 LPA
- Notice Period: - 30 days

Technical Experience

---

Q: What is the relevant experience you have in backend and frontend tech stack? (Please mention YOE separately along with tech stack) REQUIRED  
A:

- Backend Experience (3.6 years):
    - Python (Flask)
    - Node.js, NestJS
- Frontend Experience (3.6 years):
    - React, TypeScript, Next.js



---

Scale & Traffic Metrics

Q: What is the latest scale or traffic (User Interaction) that you worked on in your current/previous project? (Please provide metrics or statistical figures below) REQUIRED  
A:

Payee Validation System (Castler):

- Daily Active Users (DAU):
    - 10,000+ business users validating payees
    - 200+ enterprise clients using the platform daily
- Monthly Active Users (MAU):
    - 50,000+ unique users across organizations
    - Supporting 500+ enterprise client integrations
- Peak Concurrent Users:
    - Handling 1,000+ simultaneous validation requests
    - Supporting 5,000+ parallel validation processes
- API Requests per Day:
    - Processing 1M+ payee validation requests daily
    - Handling 100,000+ UPI/IMPS/NEFT transaction validations
    - 50,000+ bank account verifications


--- 

Product Development Experience

Q: Please tell us about the product or feature you worked on from scratch to deployment. REQUIRED  
A:

Universal API Testing Framework (Kusho)

Why I Built It

- Customers needed a single framework to test both REST and GraphQL APIs.
- Existing tools were fragmented and inefficient.
- Writing tests manually was time-consuming.
- Required automated test generation from API specifications.

Key Features

1. Custom DSL for API Testing
    - Created a custom test specification language across different API formats.
    - Used Lark (Python parsing library) for robust and flexible parsing.
    - Added syntax highlighting, autocompletion, and reusable test components.
2. Multi-Protocol Support
    - REST API Testing: Supports all HTTP methods and response validation.
    - GraphQL Testing: Handles queries, mutations, and automatic schema validation.
3. Automatic Test Generation
    - Generates tests automatically from OpenAPI/Swagger (REST) and GraphQL schemas.
    - Supports parameterized tests for broader test coverage.
4. Developer Tooling
    - VSCode Extension for test writing and editing.
    - Interactive Test Runner with real-time results.
    - Debug Console for test execution insights.

Results & Impact

- 10% faster test creation.
- 85% test coverage across different APIs.
- Unified framework for REST & GraphQL testing.
- Simplified test uploads, reducing setup complexity.

---

Database Expertise

Q: What databases have you worked on extensively? REQUIRED  
A:

MySQL

- Primary database for financial transactions at Castler.
- Key Implementations:
    - Led 500GB+ financial data migration.
    - Optimized schemas for banking data.
    - Designed high-performance transaction tables.
- Results:
    - 20% faster query performance.
    - RBI-compliant data structures.
    - Handled ₹100Cr+ monthly transactions.

MongoDB

- Used at Castler for user profiles, transaction history, and audit logs.
- Migration Expertise:
    - Zero-downtime migration.
    - Data reconciliation processes.
    - Data validation frameworks.

Redis

- Used at Kusho & Castler.
- Key Uses:
    - Caching layer for high-frequency queries.
    - Job queue management for test execution.
    - Session management & rate limiting.
- Results:
    - Sub-200ms response times.
    - 95% cache hit rates.
    - 100K+ daily operations.

Elasticsearch

- Used for search and analytics.
- Applications:
    - Test result analysis and reporting.
    - Log aggregation and searching.
    - Performance metrics visualization.
- Implemented Features:
    - Full-text search.
    - Real-time analytics dashboards.
    - Custom indexing strategies.

---

Concurrency & Performance Optimization

Q: Do you have experience working with race conditions, concurrency, or similar tools to optimize API-heavy workloads? REQUIRED  
A:

Enterprise Payment Processing Platform (Castler)

Scale

- ₹100Cr+ monthly transactions.
- High concurrency for real-time payments.

Implemented Solutions

1. Redis-based Distributed Locking
    - Used SETNX for atomic operations.
    - Configured TTL-based locks to prevent deadlocks.
    - Achieved transaction isolation for concurrent payments.
2. Database Level Optimizations
    - Row-level locking in MySQL.
    - SELECT FOR UPDATE for transaction tables.
    - Optimistic locking for account balances.
    - Indexed transaction tables for high concurrency.
3. Application Level Controls
    - Circuit breaker pattern for API rate limiting.
    - Retry mechanisms with exponential backoff.
    - Queue-based transaction processing.
    - Idempotency keys for duplicate transaction prevention.

## Suggested Related Documents
[[System Design Interview Senior Software Engineer - Harsh Tiwari.md]]\|"Technical Experience Details"

This link text effectively connects the candidate's specific experience details in the source document with the broader analysis of technical strengths in the target document, focusing on their overlapping discussion of technical capabilities and experience.]]

## Backlinks
- [[System Design Interview Senior Software Engineer - Harsh Tiwari.md]]\|Related: Instahyire.md]]

---
tags: service, systems, design, anditsasystemdesigndocument, system-designthesethreetagscoverthemainaspectsofthedocumentitsaboutanotificationsystemdesignwithinadistributedarchitecturecontext, distributed-architecture, notification-system
---
# Notification Service Design  
**Diagram**: [[Notification Service Design Deep Dive.excalidraw|🔎 Excalidraw Diagram]]  

---

## Functional Requirements  

1. **High-Volume Throughput**  
   - **1B users**  
   - Each receives **100 notifications/day** → **100B notifications/day**  
   - **1 KB/notification** → **100 TB/day** (raw data size)  

2. **No Duplicates**  
   - Must handle replay scenarios without sending the same notification multiple times.  

3. **Offline Storage & Retrieval**  
   - Store notifications if the user is offline and allow them to fetch missed messages.  

4. **Multi-Channel Delivery**  
   - **Real-Time**: WebSocket / SSE (persistent connections)  
   - **Async**: Email, SMS, push notifications, etc.  

---

## Overall Scale Math  

1. **Daily Notification Volume**:  
   - **100B** notifications/day.  
   - **~1.16M notifications/sec** on average (100B / 86,400s ≈ 1.16M/s).  
   - Peak loads could be higher (e.g., double or triple average) during certain hours.  

2. **Data Transfer**:  
   - **100 TB/day** just for notification bodies (assuming 1 KB each).  
   - Actual usage likely higher once we include protocol overhead, metadata, logs, etc.  

3. **Offline vs. Online Users**:  
   - Even if **10%** of users are offline, that’s still **10B** notifications that must be stored for later retrieval every day.  

4. **Concurrent Connections**:  
   - Potentially **millions** of active WebSocket/SSE connections at any given moment.  
   - Each server node can handle tens or hundreds of thousands of concurrent connections depending on hardware and implementation.  

5. **Storage Retention**:  
   - If we store offline notifications for, say, 7 days, that’s **700B** notifications in storage (in the worst case).  
   - Efficient compaction and TTL policies are crucial to avoid unbounded data growth.  

---

## Key Components  

### 1. **API Layer**  
- **Endpoints**:  
  - `POST /subscribe`  
    - Parameters: `topic_id`, `user_id`  
  - `POST /publish`  
    - Parameters: `topic_id`, `message`  
  - `GET /notifications`  
    - Parameters: `user_id`, optional `timestamp`  
- **Load Balancer**  
  - Uses **consistent hashing** or a similar scheme to direct requests to the correct backend service (publisher, topic service, or user consumer).  
  - Must handle up to **1M+ requests/sec** at peak.  

---

### 2. **Message Brokers**  

#### 2.1 Kafka (Topic Queues)  
- **Partitioned by `topic_id`**  
  - Each partition handles a subset of topics (or even a subset of a single large topic).  
  - The number of partitions must scale with throughput demands (e.g., 10K+ partitions if necessary).  
- **Throughput**  
  - Kafka clusters can handle **millions** of writes/sec across enough partitions.  
  - Disk-based logs enable replay for fault tolerance.  
- **Replication Factor**  
  - Typically 2–3 for high availability.  
  - Increases total disk usage to **2–3×**.  

#### 2.2 User Queues  
- **Sharded by `user_id`**  
  - Ensures all notifications for a single user end up in the same shard.  
  - Simplifies real-time delivery since the user’s WebSocket connection can be pinned to the node that processes that shard.  
- **Scale**  
  - Potentially thousands of user-queue shards to distribute load.  

---

### 3. **Stream Processing**  

#### 3.1 Fan-Out Consumers  
- **Pull from Kafka**  
  - Each consumer reads from specific topic partitions.  
  - Must handle tens or hundreds of thousands of messages/sec.  
- **Subscription Lookup**  
  - For each incoming message, retrieve all `user_id`s subscribed to that `topic_id`.  
  - Could be cached in memory or stored in a fast lookup DB (e.g., Redis, MySQL).  
- **Fan Out**  
  - Distribute notifications to the **User Queues** based on each `user_id`.  
  - Must be horizontally scalable to handle the 1.16M notifications/sec.  

#### 3.2 Idempotency Layer  
- **Why?**  
  - If a downstream service fails, Kafka replay might resend messages.  
  - We must avoid duplicating notifications to end users.  
- **Implementation**  
  - **Unique Idempotency Key**: Generate a random UUID per notification.  
  - **Bloom Filter**:  
    - Quick in-memory check to see if a key has been processed before.  
    - If not present, process and insert the key; if present, skip.  
    - Memory usage can become large with **100B+** keys/day; consider multi-layer approach (e.g., rotating Bloom filters daily, persisting older data to disk, etc.).  
  - **False Positives**  
    - Bloom filters can occasionally flag a new key as “seen.”  
    - Tolerable if the false-positive rate is low or if a second check (e.g., in a distributed cache) is performed.  

---

### 4. **Delivery Services**  

#### 4.1 Real-Time (WebSocket / SSE)  
- **Persistent Connections**  
  - Each user has exactly one open connection to the service that handles their `user_id` shard.  
- **Scale**  
  - If we assume **10M** concurrent online users, we must distribute these connections across enough consumer nodes (e.g., 100 nodes each handling 100K connections).  
- **High Throughput**  
  - Each node can push thousands of notifications/sec to active connections.  

#### 4.2 Async Channels (Email / SMS)  
- **Downstream Microservices**  
  - Pick up messages from the **User Queues** or an intermediary queue (e.g., RabbitMQ) dedicated to email/SMS tasks.  
  - Must handle large daily volumes (potentially billions of emails/SMS).  
  - Enforce rate-limits to avoid blacklisting by email providers or carriers.  

#### 4.3 Offline Storage (HBase)  
- **Volume**  
  - Potentially **10B**+ offline notifications/day (if 10% of users are offline).  
  - With a 7-day retention, that’s up to **70B** stored messages at any given time (in the worst case).  
- **Schema**  
  - **Row Key**: `user_id + timestamp` (or reversed timestamp).  
  - Allows fast range scans for missed notifications in chronological order.  
- **Throughput**  
  - HBase can handle **tens of thousands** of writes/sec per region server.  
  - Scale horizontally by adding region servers.  
- **Reads**  
  - When an offline user returns, the system queries HBase for all notifications since their last seen timestamp.  

---

### 5. **Databases**  

#### 5.1 MySQL (Topics / Subscriptions)  
- **Subscription Data**  
  - Could have up to **1B** users × multiple topics.  
  - Each subscription row: `(topic_id, user_id)`.  
- **Sharding**  
  - Likely needed if we have billions of subscription rows.  
  - Strong consistency ensures accurate subscription data (no stale reads).  

#### 5.2 HBase (Notifications)  
- **Offline Notifications**  
  - Write-heavy workload (10B+ writes/day possible).  
  - Column-oriented design + LSM trees → efficient ingestion and compaction.  
- **Region Splits**  
  - Start with a certain number of regions, then split automatically as data grows.  
  - Properly distributing `user_id` range avoids hotspots.  

---

## Data Flow (Refer to Excalidraw Diagram)  

1. **Publish**  
2. 1. Client calls `POST /publish` with `topic_id` + `message`.  
3. 2. Load Balancer → **Publisher Service** → **Kafka** (partitioned by `topic_id`).  

4. **Fan-Out**  
5. 1. **Fan-Out Consumers** read from Kafka.  
6. 2. For each message, lookup all subscribed `user_id`s.  
7. 3. Perform **idempotency** checks (Bloom filter).  
8. 4. Push the message to **User Queues** (sharded by `user_id`).  

9. **Delivery**  
10. 1. **User Queue Consumers** pick up the notification.  
11. 2. If **user is online**, send via WebSocket/SSE.  
12. 3. If **user is offline**, store in **HBase**.  
13. 4. Optionally, forward to Email/SMS microservices for asynchronous delivery.  

14. **Fetch**  
15. 1. Offline user returns, calls `GET /notifications?user_id=XYZ`.  
16. 2. Query **HBase** by `user_id + timestamp` to retrieve missed messages.  
17. 3. Return them to the client.  

---

## Design Decisions and Detailed Scale Math  

1. **Kafka Partitioning Strategy**  
   - We have **100B messages/day** → ~1.16M messages/sec on average.  
   - Each partition can handle up to tens or hundreds of thousands of writes/sec (depending on hardware).  
   - We might configure **1K–10K partitions** to comfortably handle peak loads with headroom.  

2. **Fan-Out Throughput**  
   - After a message is read from Kafka, we could be sending it to thousands or millions of subscribers (depending on the topic).  
   - This **fan-out** step must be massively parallel, likely requiring a **distributed** cluster (e.g., dozens or hundreds of consumer instances).  
   - Caching subscription data (e.g., in Redis or memory) to avoid constant DB lookups.  

3. **Bloom Filter Memory Footprint**  
   - If we track **100B unique notifications/day**, and each notification has a unique idempotency key:  
     - A naive Bloom filter for 100B items with a 1% false-positive rate can require gigabytes of memory.  
     - We might **rotate** Bloom filters daily or even hourly, archiving old keys to disk to reduce memory usage.  
     - Alternatively, we can store only recent (e.g., last few hours) keys in the Bloom filter, then do a fallback check in a fast store (e.g., RocksDB, Redis).  

4. **HBase Region Servers**  
   - If **10B** notifications go offline daily, that’s ~115K writes/sec (10B / 86,400 ≈ 115,740).  
   - Peak loads might be higher (2–3× average).  
   - Each region server can handle tens of thousands of writes/sec. We might need **dozens** of region servers.  
   - Each server might store 1–2 TB (or more) before region splits; with a 7-day retention, we’d need enough total capacity for up to 700 TB (plus replication overhead).  

5. **WebSocket/SSE Connections**  
   - If **10M** users are online concurrently, we need enough consumer nodes to handle 10M connections.  
   - If each node can handle 100K connections, that’s ~100 nodes for just the connections.  
   - Each node also processes incoming messages from the user queue, requiring robust CPU/memory.  

6. **MySQL Subscription Table**  
   - Potentially **billions** of rows (`(topic_id, user_id)` pairs).  
   - We may shard by `topic_id` or by `user_id`, or both (e.g., a multi-tenant approach).  
   - Writes are less frequent than for notifications, but queries must be fast during fan-out.  
   - Consider caching in Redis or a specialized in-memory store to reduce direct MySQL lookups at runtime.  

---

## Related Notes  
- [[Idempotency in Distributed Systems]]  
- [[Kafka vs RabbitMQ]]  
- [[WebSocket Connection Management]]  
- [[Data Sharding Strategies]]  

---

## Summary  

This **Notification Service** design addresses **100B daily notifications** for **1B users**, leveraging:  
- **Kafka** for high-throughput, log-based ingestion and replay.  
- **Fan-Out Consumers** that distribute messages from topic partitions to user-specific queues, ensuring each user’s notifications are funneled to the correct consumer node.  
- **Idempotency** (unique keys + Bloom filters) to avoid duplicates during replay.  
- **Real-Time Delivery** (WebSocket/SSE) when users are online, requiring millions of persistent connections across a horizontally scaled cluster.  
- **Offline Storage** in **HBase** (column-oriented NoSQL) for missed messages, capable of ingesting billions of writes per day with fast lookups by `user_id + timestamp`.  
- **MySQL** (or similarly sharded relational store) for strong-consistency subscription data.  

**Key Scale Points**:  
- **~1.16M messages/sec** on average, peaking higher.  
- **100 TB/day** data ingestion.  
- **Millions** of concurrent connections for real-time delivery.  
- **10B**+ offline notifications daily, requiring efficient storage and retrieval.  

With proper **sharding**, **horizontal scaling**, **distributed caching**, and **monitoring**, this design can handle global-scale notification delivery while preventing duplicates, delivering real-time messages, and reliably storing offline notifications.  


## Suggested Related Documents
[[AWS Services Deep Dive]]
[[AWS Services Deep Dive.md"Notification Architecture Components"

This link text effectively connects the two documents by highlighting that one describes a notification service design while the other details the AWS services that could implement such a system, focusing on their shared architectural context.]]

## Backlinks
- [[AWS Services Deep Dive.md]]\|"AWS Notification System Architecture"

This link text effectively connects the documents by referencing both the AWS services context from the source and the notification system focus of the target, while remaining concise and descriptive.]]

#distributed-systems #api-design #url-shortener #system-design

#system-design #distributed-systems #url-shortener #api-design

## Introduction
A URL shortener converts long URLs into shorter, manageable links. Key challenges include handling high traffic, ensuring low latency, avoiding collisions, and scaling efficiently. This document synthesizes strategies from two expert transcripts to outline a robust design.

---

## Functional & Non-Functional Requirements

### Functional
- **Create Short URL**: Convert a long URL into a short, unique identifier.
- **Redirect to Long URL**: Resolve a short URL to its original long URL.

### Non-Functional
- **Low Latency**: Redirects must be fast (milliseconds).
- **High Availability**: 99.9% uptime.
- **Scalability**: Handle 1,000+ writes/sec and 10:1 read/write ratio.

---

## API Design
- **POST /create**
  - Input: `{ "long_url": "..." }`
  - Output: `{ "short_url": "..." }` (HTTP 201)
- **GET /{short_url}**
  - Redirects to long URL with HTTP 301 (Permanent Redirect).

---

## Data Capacity Modeling

### Assumptions
- **30M users/month**, 7-character short URLs.
- **Data per entry**: 2.03 KB (long URL, short URL, timestamps).

### Storage Calculations
- Monthly: 30M entries × 2.03 KB ≈ **60.7 GB**.
- Yearly: **0.7 TB**.
- 5 Years: **3.6 TB**.

---

## URL Encoding Techniques

### Base62 Encoding
- **Characters**: `[a-zA-Z0-9]` (62 total).
- **Advantages**: 
  - 7 characters → 62⁷ ≈ **3.5 trillion** unique URLs.
  - Avoids collisions with sequential counters.
- **Example Code**:
  ```python
  def base62_encode(num):
      chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
      result = []
      while num > 0:
          num, rem = divmod(num, 62)
          result.append(chars[rem])
      return ''.join(reversed(result))
```
### MD5 Hashing (Not Recommended)

- Produces 128-bit hash (32 hex chars). Truncating to 7 chars risks collisions.
    
- **Collision Handling**: Requires DB checks, which are inefficient at scale.
    

---

## Database Considerations

### SQL vs. NoSQL

| **SQL (e.g., PostgreSQL)** | **NoSQL (e.g., Cassandra)** |
| -------------------------- | --------------------------- |
| ACID compliance            | High scalability            |
| Complex to shard           | Built-in replication        |
| Single-point failure risk  | Eventual consistency        |

**Decision**: Use **NoSQL** for write scalability and distributed storage.

---

## Distributed Coordination with ZooKeeper

### Role of ZooKeeper

- **Range Allocation**: Assigns unique counter ranges to app servers (e.g., Server 1: 0–1M, Server 2: 1M–2M).
    
- **Collision Prevention**: Servers generate short URLs within their assigned range, eliminating DB checks.
    
- **Fault Tolerance**: If a server dies, its range is marked unused (minimal ID loss).
    

### Workflow

1. **Server Registration**: New app servers request a range from ZooKeeper.
    
2. **Counter Exhaustion**: Servers get new ranges when their current range is depleted.
    
3. **Scalability**: Horizontally scale app servers without overlapping ranges.
    

---

## Caching Strategy

- **Redis/Memcached**: Cache frequent short URL → long URL mappings.
    
- **Cache Invalidation**: TTL (e.g., 24h) or LRU eviction.
    
- **Benefits**: Reduces DB read load by 90%+.
    

---

## Additional Features

### Analytics

- Track clicks, geographic data, and referral sources.
    
- **Tools**: Elasticsearch for logs, Google Analytics for basic metrics.
    

### Security

- **Rate Limiting**: Prevent abuse (e.g., 100 requests/minute/IP).
    
- **Random Suffixes**: Add 2–3 random chars to short URLs to deter prediction.
    

### Expiration

- Optional TTL for short URLs (e.g., 1 year).
    

---

## System Diagram



User → Load Balancer → App Servers → ZooKeeper (Range Mgmt)
                          ↓
                       Cache (Redis)
                          ↓
                      NoSQL DB (Cassandra)

---

## Conclusion

- **Core Components**: Base62 encoding, ZooKeeper for range coordination, NoSQL DB, caching.
    
- **Scalability**: Horizontal scaling of app servers and databases.
    
- **Trade-offs**: Eventual consistency (NoSQL) vs. ACID (SQL), slight ID loss for fault tolerance.
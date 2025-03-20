#test-automation #dsl-framework #api-testing #testing-framework #dsl-design

#test-automation #dsl-framework #api-testing

A declarative, multi-protocol API testing framework with a custom DSL for REST/GraphQL, supporting data-driven testing, inline setup/teardown, and dynamic assertions.

---

## Table of Contents
1. [DSL Syntax](#dsl-syntax)
2. [Key Features](#key-features)
   - [Assertions](#assertions)
   - [Variables & Templating](#variables--templating)
   - [Loops](#loops)
   - [Setup & Teardown](#setup--teardown)
3. [Implementation](#implementation)
   - [Lark Grammar](#lark-grammar)
   - [Pydantic Models](#pydantic-models)
   - [Test Runner](#test-runner)
4. [Advanced Features](#advanced-features)
   - [Conditional Assertions](#conditional-assertions)
   - [Parallel Execution](#parallel-execution)
   - [Error Handling](#error-handling)
5. [CLI Commands](#cli-commands)
6. [Examples](#examples)
7. [Benefits](#benefits)

---

## DSL Syntax

### Basic Structure
```python
test "User lifecycle" {
  protocol: rest
  setup {
    request { 
      method POST
      path "/users"
      body { "name": "Test User" }
    }
    assert { status_code 201 }
    extract "user_id" from "$.id"  // Variable extraction
  }
  request {
    method GET
    path "/users/{{user_id}}"
  }
  assert {
    status_code 200
    json_path "$.name" equals "Test User"
  }
  teardown {
    request { method DELETE; path "/users/{{user_id}}" }
    assert { status_code 204 }
  }
}
```

---

## Key Features

### Assertions
- **Status Codes**: `status_code 200`
- **JSON Paths**: `json_path "$.name" equals "John Doe"`
- **GraphQL Data**:
  ```python
  assert {
    data { user { id "1" name "John Doe" } }
  }
  ```
- **Regex**: `json_path "$.email" regex ".*@example.com"`
- **Type Checks**: `json_path "$.id" type "number"`

### Variables & Templating
- **Context Variables**: `{{user_id}}` (extracted from responses or environment)
- **Environment Variables**:
  ```python
  setup {
    env { API_KEY: "secret" }
    request { headers { "Authorization": "Bearer {{API_KEY}}" } }
  }
  ```

### Loops
```python
test "Check users" {
  for user_id in [1, 2, 3] {
    request { method GET; path "/users/{{user_id}}" }
    assert { status_code 200 }
  }
}
```

### Setup & Teardown
- **Inline Logic**:
  ```python
  setup {
    request { method POST; path "/users" }
    assert { status_code 201 }
    extract "user_id" from "$.id"  // Store for later use
  }
  teardown {
    request { method DELETE; path "/users/{{user_id}}" }
  }
  ```

---

## Implementation

### Lark Grammar
Full grammar for parsing the DSL (`grammar.lark`):
```lark
start: test_case+

test_case: "test" ESCAPED_STRING "{" 
          [protocol_section] 
          [setup_section] 
          request_section 
          (assert_section)+ 
          [teardown_section] 
          "}"

protocol_section: "protocol" ":" ("rest" | "graphql")

// Request Sections
request_section: "request" "{" (method | path | query | headers | variables | body)* "}"
method: "method" ("GET" | "POST" | "PUT" | "DELETE" | "PATCH")
path: "path" ESCAPED_STRING
query: "query" ESCAPED_STRING
headers: "headers" "{" (header_pair)* "}"
header_pair: ESCAPED_STRING ":" ESCAPED_STRING
variables: "variables" "{" (variable_pair)* "}"
variable_pair: ESCAPED_STRING ":" (ESCAPED_STRING | NUMBER)
body: "body" "{" (json_key_value)* "}"
json_key_value: ESCAPED_STRING ":" (ESCAPED_STRING | NUMBER | "{" json_key_value "}")

// Assertions
assert_section: "assert" "{" (status_code_assertion | json_path_assertion | graphql_assertion | conditional_assertion)* "}"
status_code_assertion: "status_code" NUMBER
json_path_assertion: "json_path" ESCAPED_STRING ("equals" | "regex" | "type") (ESCAPED_STRING | NUMBER | CNAME)
graphql_assertion: "data" "{" (graphql_field_assertion)* "}"
graphql_field_assertion: ESCAPED_STRING "{" (graphql_field_assertion | value_assertion)* "}"
value_assertion: ESCAPED_STRING (ESCAPED_STRING | NUMBER)

// Setup/Teardown
setup_section: "setup" "{" (request_section | assert_section | extract_section)+ "}"
teardown_section: "teardown" "{" (request_section | assert_section | extract_section)+ "}"
extract_section: "extract" CNAME "from" ESCAPED_STRING

// Conditionals
conditional_assertion: "if" condition "{" assert_section "}" ["else" "{" assert_section "}"]
condition: json_path_assertion | graphql_assertion

// Loops
loop_section: "for" CNAME "in" "[" (NUMBER | ESCAPED_STRING) ("," (NUMBER | ESCAPED_STRING))* "]" "{" (request_section | assert_section)+ "}"

// Terminals
%import common.ESCAPED_STRING
%import common.NUMBER
%import common.CNAME
%import common.WS
%ignore WS
```

### Pydantic Models
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RequestModel(BaseModel):
    method: str
    path: str
    headers: Dict[str, str] = {}
    body: Optional[Dict] = None

class AssertionModel(BaseModel):
    type: str  # "status_code", "json_path", etc.
    path: Optional[str] = None  # JSON/GraphQL path
    expected: Any

class TestStep(BaseModel):
    request: Optional[RequestModel] = None
    assertions: List[AssertionModel] = []
    extracts: Dict[str, str] = {}  # {"user_id": "$.id"}

class TestCaseModel(BaseModel):
    name: str
    protocol: str
    setup: Optional[TestStep] = None
    request: RequestModel
    assertions: List[AssertionModel]
    teardown: Optional[TestStep] = None
```

### Test Runner
```python
import httpx
from jsonpath_ng import parse

def execute_test(test_case: TestCaseModel, base_url: str):
    context = {}
    
    # Setup
    if test_case.setup:
        response = httpx.request(
            method=test_case.setup.request.method,
            url=f"{base_url}{test_case.setup.request.path}",
            headers=test_case.setup.request.headers
        )
        for assertion in test_case.setup.assertions:
            validate_assertion(response, assertion)
        for var_name, json_path in test_case.setup.extracts.items():
            context[var_name] = parse(json_path).find(response.json())[0].value
    
    # Main Test
    response = httpx.request(
        method=test_case.request.method,
        url=f"{base_url}{test_case.request.path}",
        headers=test_case.request.headers
    )
    for assertion in test_case.assertions:
        validate_assertion(response, assertion)
    
    # Teardown
    if test_case.teardown:
        httpx.request(
            method=test_case.teardown.request.method,
            url=f"{base_url}{test_case.teardown.request.path}",
            headers=test_case.teardown.request.headers
        )
```

---

## Advanced Features

### Conditional Assertions
```python
assert {
  if json_path "$.user.role" equals "admin" {
    json_path "$.permissions" type "array"
  } else {
    json_path "$.error" equals "Access denied"
  }
}
```

### Parallel Execution
```python
import asyncio

async def run_tests_parallel(test_cases: List[TestCaseModel]):
    async with httpx.AsyncClient() as client:
        tasks = [execute_test_case(tc, client) for tc in test_cases]
        await asyncio.gather(*tasks)
```

### Error Handling
- **Syntax Errors**:
  ```bash
  Syntax error at line 5, column 3:
    4 |     request {
    5 |         methods GET
                ^
  Expected one of: method, path, query, headers, variables
  ```
- **Assertion Failures**:
  ```bash
  Assertion failed: json_path "$.name" → "John" != "Jane"
  ```

---

## CLI Commands
Built with **Typer** for a user-friendly interface:
```bash
# Import artifacts to DSL
$ python cli.py import-postman collection.json --output tests.dsl
$ python cli.py import-openapi spec.yaml --output tests.dsl

# Run tests
$ python cli.py run tests.dsl --vars API_KEY=secret

# Generate coverage report
$ python cli.py coverage tests.dsl --format html
```

| Command                | Description                          |
|------------------------|--------------------------------------|
| `import-postman`       | Convert Postman collection to DSL    |
| `import-openapi`       | Convert OpenAPI spec to DSL          |
| `run`                  | Execute tests                        |
| `coverage`             | Generate coverage report             |

---

## Examples

### GraphQL Test with Variables
```python
test "Fetch user" {
  protocol: graphql
  request {
    query {
      user(id: $id) { id, name }
    }
    variables { id: "1" }
  }
  assert {
    data { user { id "1" name "John Doe" } }
  }
}
```

### Data-Driven Test
```python
test "Check prices" {
  for product_id in ["p1", "p2", "p3"] {
    request { method GET; path "/products/{{product_id}}" }
    assert {
      json_path "$.price" greater_than 0
    }
  }
}
```

---

## Benefits
- **Unified Syntax**: Test REST, GraphQL, and future protocols in one DSL.
- **Self-Documenting**: Tests mirror API specifications.
- **Extensible**: Add new assertion types or protocols via plugins.
- **CI/CD Ready**: Integrates with pytest, GitHub Actions, etc.
- **Debugging Tools**: Detailed error logs and request/response captures.

---

This framework combines the expressiveness of a custom DSL with Python’s robustness, enabling teams to automate API testing at scale.

## Suggested Related Documents
[[Intelligent Task Processing System - Interview Analysis.md]]\|"API Testing Architecture Evolution"

This link text connects the documents by highlighting how the universal testing framework naturally evolves into the larger distributed test generation system, while keeping the focus on API testing and architecture.]]

## Backlinks
- [[Intelligent Task Processing System - Interview Analysis.md]]\|Related: Universal API Testing Framework.md]]

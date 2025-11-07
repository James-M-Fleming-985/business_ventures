# Testing Guide

## TDD (Test-Driven Development) Approach

This project follows Test-Driven Development principles:
1. Write tests first
2. Implement features
3. Run tests to verify
4. Refactor with confidence

## Test Structure

Tests are organized to mirror the source code structure:
- `01-SHARED/` tests → `04-TESTS/Shared/`
- `02-SERVER/` tests → `04-TESTS/Server/`
- `03-CLIENT/` tests → `04-TESTS/Client/`

## Running Tests

### In Roblox Studio:

1. Copy test files to `ServerScriptService/Tests/`
2. Create a test runner script:

```lua
local Tests = ServerScriptService.Tests
for _, testModule in ipairs(Tests:GetChildren()) do
    if testModule:IsA("ModuleScript") then
        local test = require(testModule)
        test.RunAll()
    end
end
```

3. Run the script from Command Bar

### Test Output:

Tests will print results in this format:
```
✅ PASS: Utils.FormatNumber with 1000
✅ PASS: Utils.FormatNumber with 1000000
❌ FAIL: Utils.DeepCopy with nested tables
   Expected: {a = {b = 1}}
   Got: {a = {b = 2}}
```

## Writing Tests

### Example Test File:

```lua
local TestSuite = {}

function TestSuite.TestFormatNumber()
    local Utils = require(game.ReplicatedStorage.Shared.Utils)
    
    -- Test case 1
    local result = Utils.FormatNumber(1000)
    assert(result == "1,000", "Expected 1,000")
    
    -- Test case 2
    local result2 = Utils.FormatNumber(1000000)
    assert(result2 == "1,000,000", "Expected 1,000,000")
end

function TestSuite.RunAll()
    local tests = {
        "TestFormatNumber",
        -- Add more tests here
    }
    
    for _, testName in ipairs(tests) do
        local success, error = pcall(TestSuite[testName])
        if success then
            print("✅ PASS:", testName)
        else
            warn("❌ FAIL:", testName, error)
        end
    end
end

return TestSuite
```

## Test Categories

### Unit Tests
Test individual functions in isolation.
Example: `Utils.FormatNumber()`, `Utils.Clamp()`

### Integration Tests
Test how modules work together.
Example: `CatManager` using `DataStore` and `CurrencyManager`

### System Tests
Test complete workflows.
Example: Player joins → gets starter cat → trains cat → plays mini-game

## Common Test Patterns

### Testing Pure Functions:
```lua
function TestPureFunction()
    local input = 5
    local expected = 10
    local result = MyModule.Double(input)
    assert(result == expected, "Expected " .. expected)
end
```

### Testing with Mock Data:
```lua
function TestWithMock()
    local mockPlayer = {UserId = 123, Name = "TestPlayer"}
    local mockData = DataStore.CreateDefaultData(mockPlayer)
    assert(mockData.Currency > 0, "Should have starting currency")
end
```

### Testing Asynchronous Code:
```lua
function TestAsync()
    local completed = false
    task.spawn(function()
        -- Do async work
        task.wait(1)
        completed = true
    end)
    
    task.wait(2)
    assert(completed, "Should have completed")
end
```

## Coverage Goals

- ✅ **High Priority**: Core systems (DataStore, CatManager, CurrencyManager) - 80%+ coverage
- ✅ **Medium Priority**: Game logic (MiniGameManager, SanctuaryManager) - 60%+ coverage  
- ✅ **Low Priority**: UI controllers - 40%+ coverage

## Continuous Testing

Run tests:
- Before committing code
- After making changes to core systems
- Before releasing updates
- When bugs are reported (write test first, then fix)

## Test Files Included

See `04-TESTS/` folder for:
- ✅ `Utils_Test.lua` - Utility function tests
- ✅ `Config_Test.lua` - Configuration validation
- ✅ `DataStore_Test.lua` - Data persistence tests
- ✅ `CatManager_Test.lua` - Cat system tests
- ✅ `CurrencyManager_Test.lua` - Currency tests

## Debugging Failed Tests

1. Read the error message carefully
2. Check expected vs actual values
3. Add print statements in the implementation
4. Run test in isolation
5. Verify test data is correct

## Best Practices

- ✅ Keep tests simple and focused
- ✅ One assertion per test when possible
- ✅ Use descriptive test names
- ✅ Test edge cases (0, negative, nil, empty)
- ✅ Clean up after tests (remove test data)
- ❌ Don't test Roblox APIs directly
- ❌ Don't make tests dependent on each other
- ❌ Don't use production DataStores in tests

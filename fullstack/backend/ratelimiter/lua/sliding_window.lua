-- This script runs ATOMICALLY inside Redis.
-- Atomic means no other command can interrupt it while it runs,
-- which prevents race conditions between concurrent requests.

local key = KEYS[1]              -- Redis key for this user+ip+route combo
local now = tonumber(ARGV[1])    -- current timestamp in milliseconds
local windowMs = tonumber(ARGV[2]) -- window size in milliseconds
local limit = tonumber(ARGV[3])  -- request limit
local sequenceKey = key .. ":seq"

-- 1. Remove all timestamps older than our window
redis.call("ZREMRANGEBYSCORE", key, 0, now - windowMs)

-- 2. Count how many requests are left in the window
local currentCount = redis.call("ZCARD", key)

-- 3. Decide - allowed or blocked
if currentCount < limit then
    -- allowed: add this request's timestamp to the sorted set.
    -- score = timestamp, member = unique request id. Use a per-key
    -- sequence so multiple requests in the same millisecond don't collide.
    local sequence = redis.call("INCR", sequenceKey)
    redis.call("ZADD", key, now, tostring(now) .. "-" .. tostring(sequence))

    -- set TTL so Redis auto-cleans the key after the window expires,
    -- preventing memory leaks for inactive users
    redis.call("EXPIRE", key, math.ceil(windowMs / 1000))
    redis.call("EXPIRE", sequenceKey, math.ceil(windowMs / 1000))

    return { 1, limit - currentCount - 1 }
else
    -- blocked: don't add anything, just report it
    return { 0, 0 }
end

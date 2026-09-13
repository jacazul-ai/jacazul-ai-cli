const std = @import("std");

/// A generic is a function that returns a type.
fn Ring(comptime T: type, comptime capacity: usize) type {
    return struct {
        items: [capacity]T = undefined,
        head: usize = 0,
        len: usize = 0,

        const Self = @This();

        pub fn push(self: *Self, value: T) error{Full}!void {
            if (self.len == capacity) return error.Full;
            self.items[(self.head + self.len) % capacity] = value;
            self.len += 1;
        }

        pub fn pop(self: *Self) ?T {
            if (self.len == 0) return null;
            const value = self.items[self.head];
            self.head = (self.head + 1) % capacity;
            self.len -= 1;
            return value;
        }
    };
}

test "comptime parameters build a concrete type" {
    var ring: Ring(u8, 2) = .{};
    try ring.push(1);
    try ring.push(2);
    try std.testing.expectError(error.Full, ring.push(3));
    try std.testing.expectEqual(@as(?u8, 1), ring.pop());
}

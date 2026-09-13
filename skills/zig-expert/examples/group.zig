const std = @import("std");
const Io = std.Io;

fn square(out: *u64, n: u64) void {
    out.* = n * n;
}

test "a Group owns the lifetime of its tasks" {
    const io = std.testing.io;
    var results: [4]u64 = undefined;
    var group: Io.Group = .init;
    defer group.cancel(io);

    for (&results, 0..) |*slot, i| {
        group.async(io, square, .{ slot, @as(u64, i) });
    }
    try group.await(io);
    try std.testing.expectEqualSlices(u64, &.{ 0, 1, 4, 9 }, &results);
}

const std = @import("std");
const Allocator = std.mem.Allocator;

/// Caller owns the returned slice and frees it with the same allocator.
pub fn joinWords(gpa: Allocator, words: []const []const u8) Allocator.Error![]u8 {
    var out: std.ArrayList(u8) = .empty;
    errdefer out.deinit(gpa);

    for (words, 0..) |word, i| {
        if (i != 0) try out.append(gpa, ' ');
        try out.appendSlice(gpa, word);
    }
    return out.toOwnedSlice(gpa);
}

test "joinWords returns an owned slice" {
    const gpa = std.testing.allocator;
    const joined = try joinWords(gpa, &.{ "zig", "0.16" });
    defer gpa.free(joined);
    try std.testing.expectEqualStrings("zig 0.16", joined);
}

test "joinWords releases partial work on failure" {
    try std.testing.checkAllAllocationFailures(
        std.testing.allocator,
        struct {
            fn run(gpa: Allocator) !void {
                const joined = try joinWords(gpa, &.{ "a", "b", "c" });
                defer gpa.free(joined);
            }
        }.run,
        .{},
    );
}

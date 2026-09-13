const std = @import("std");

const ParseError = error{ Empty, NotANumber };

fn parsePort(text: []const u8) ParseError!u16 {
    if (text.len == 0) return error.Empty;
    return std.fmt.parseInt(u16, text, 10) catch error.NotANumber;
}

test "error sets are part of the contract" {
    try std.testing.expectEqual(@as(u16, 8080), try parsePort("8080"));
    try std.testing.expectError(error.Empty, parsePort(""));
    try std.testing.expectError(error.NotANumber, parsePort("http"));
}

const std = @import("std");
const Io = std.Io;

/// Accept an *Io.Writer so the caller decides where output goes.
fn report(w: *Io.Writer, name: []const u8, count: usize) Io.Writer.Error!void {
    try w.print("{s}: {d}\n", .{ name, count });
}

test "writers are injected, not global" {
    var buffer: [64]u8 = undefined;
    var fixed: Io.Writer = .fixed(&buffer);
    try report(&fixed, "items", 3);
    try std.testing.expectEqualStrings("items: 3\n", fixed.buffered());
}

test "reading a file goes through Io" {
    const io = std.testing.io;
    const gpa = std.testing.allocator;
    var tmp = std.testing.tmpDir(.{});
    defer tmp.cleanup();
    try tmp.dir.writeFile(io, .{ .sub_path = "hello.txt", .data = "hi\n" });
    const bytes = try tmp.dir.readFileAlloc(io, "hello.txt", gpa, .limited(1024));
    defer gpa.free(bytes);
    try std.testing.expectEqualStrings("hi\n", bytes);
}

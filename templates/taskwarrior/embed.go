// Package taskwarrior embeds the Taskwarrior configuration templates the
// launcher installs and syncs UDAs from.
package taskwarrior

import _ "embed"

// Caged is the template whose UDAs are synced into an inherited TASKRC.
//
//go:embed caged/.taskrc
var Caged string

// Unhinged is the template for the Jacazul-owned .taskrc.
//
//go:embed unhinged/.taskrc
var Unhinged string

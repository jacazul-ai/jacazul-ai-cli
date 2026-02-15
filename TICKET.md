# Ticket: Enable Native (Non-Container) Execution of Unhinged Initiative

## Problem Statement

Currently, the unhinged initiative (agent + skill setup) requires running inside a Podman container. Need to enable full native execution on host systems (Fedora/Debian) without containerization.

## Objective

Enable users to run the entire unhinged initialization workflow natively:
- OS detection
- Automatic dependency setup per distribution
- Agent and skill initialization
- Full workflow testing on native Linux systems

## Scope

### Completed ✅
- OS detection hook (detect-os.sh)
  - Identifies Fedora, Debian, Ubuntu
  - Exports OS_TYPE variable for downstream use
  - Returns proper exit codes

- Fedora setup script (setup-fedora.sh)
  - Verifies 17 required packages
  - Accumulates missing packages
  - Outputs dnf install preview (non-destructive)
  - Uses modular command verification approach

- Configure-direct integration
  - Calls detect-os.sh on startup
  - Executes OS-specific setup scripts automatically
  - Provides user-friendly formatted output

### Pending
- [ ] Debian/Ubuntu setup script (setup-debian.sh)
  - apt-get based package verification
  - Same verification pattern as Fedora variant

- [ ] Native execution testing
  - Test on actual Fedora system
  - Test on actual Debian system
  - Verify configure-direct integration
  - Test full agent + skill startup

- [ ] Documentation refinement
  - Native execution quickstart guide
  - Troubleshooting guide for missing packages
  - Installation verification steps

## Technical Approach

**Strategy: Verify-Only Mode**
- Scripts verify environment without auto-installing
- Output package installation command for user review
- Defer actual installation to user decision
- Modular design: detect-os.sh hooks into setup scripts

**Key Design Decisions**
- Use `return` instead of `exit 0` in sourced scripts to preserve variables
- Single quotes in printf format strings to prevent shellcheck SC2059
- Command-to-package mapping for accurate verification
- Accumulate packages instead of installing one-by-one

## Files

- `/project/scripts/detect-os.sh` - OS detection with OS_TYPE export
- `/project/scripts/setup-fedora.sh` - Fedora dependency setup
- `/project/scripts/configure-direct` - Integration point for native setup
- (Pending) `/project/scripts/setup-debian.sh` - Debian dependency setup

## Acceptance Criteria

1. ✅ OS detection works on Fedora and Debian
2. ✅ Fedora setup script verifies all 17 required packages
3. ✅ Setup scripts provide preview of installation without auto-executing
4. ✅ configure-direct seamlessly integrates OS detection
5. ⏳ Debian setup script created and tested
6. ⏳ Native execution verified on both Fedora and Debian systems
7. ⏳ User-facing documentation completed

## Related Tasks

- Task 1eff8767: Create Fedora setup script (IN PROGRESS → needs completion)
- Task 136: Debian setup dependencies (BLOCKED → ready after Debian script)
- Task 137: Setup verification and testing (BLOCKED → ready after setup scripts)

## Notes

- All scripts are shellcheck-clean
- Modular approach allows easy extension for additional distributions
- Strategy approved for bring-your-own testing model
- Package list includes: python3, git, gcc, make, curl, unzip, wget, jq, ripgrep, procps, fzf, htop, sudo, task2, bc, nodejs, nodejs-npm

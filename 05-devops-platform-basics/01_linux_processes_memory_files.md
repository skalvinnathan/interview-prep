# 01. Linux: processes, memory, and files

How to read this file:
- Short sentences. Every new word is explained the first time.
- `[REAL]` means I ran the command on this Mac (macOS 26, Apple chip) on 2026-11-15 and pasted the output.
- `[SAMPLE]` means typical Linux output that I wrote to show the shape. The numbers are made up. I did not run it here, because this Mac is not Linux.
- Mac and Linux are close cousins (both follow the "Unix" way). The ideas are the same. Some command names differ. I say so when it matters.

---

## 1. What it is (plain words + analogy)

Linux is the operating system (OS) that sits between your programs and the computer parts (CPU, memory, disk, network). The OS gives each program a safe little room to work in.

Analogy: a big hotel.
- The **kernel** is the hotel manager. It owns all rooms, water, and electricity.
- A **process** is a guest in a room. A guest has an ID number (PID), a room (its memory), and a key list (open files).
- A **signal** is a note slid under the door ("please leave", or "leave NOW").
- **Memory (RAM)** is the hotel's fast desk space. **Disk** is the slow warehouse in the basement.
- The **page cache** is the manager keeping popular warehouse boxes on the front desk, so guests do not wait.

Words you need:
- **Process**: a running program. It has a number called **PID** (process ID).
- **PPID**: the PID of the parent (the process that started it).
- **System call (syscall)**: a request from a program to the kernel ("open this file", "start a new process").
- **File descriptor (fd)**: a small number that stands for an open file, pipe, or network connection.
- **Inode**: the record on disk that stores a file's facts (size, owner, where the data blocks are). The file name is stored separately, in the directory.

## 2. Why it matters in interviews

Platform and SRE jobs are "what is really happening under the container?" jobs. Every Kubernetes problem ends in Linux: a pod is killed because of the OOM killer, a pod will not stop because PID 1 ignores signals, a disk is "full" but `du` shows nothing, a service says "too many open files". Interviewers use these small Linux questions to check whether you understand the base, not only the tools on top. Smallest AI says its call tests fundamentals, so this file is high value.

## 3. How it works, step by step

### 3.1 Starting a program: fork and exec

To run a new program, Linux does two steps:

1. `fork()` makes a near-copy of the current process. Now there are two: parent and child. (The kernel copies memory lazily, only when someone writes. This is called copy-on-write.)
2. `exec()` makes the child **become** a different program. Same PID, new program code.

```
 shell (PID 100)
   |
   | fork()
   v
 shell copy (PID 101)  --exec("ls")-->  now it IS "ls" (still PID 101)
   |
   | exit(0)
   v
 shell (PID 100) calls wait() and learns "101 finished with code 0"
```

Why two steps? Between fork and exec the child can set things up (redirect output, drop rights). This is how shells and container runtimes work.

**Zombie**: a child that has finished, but the parent has not yet called `wait()` to read its exit code. The kernel keeps a tiny record. Nothing runs. It shows as state `Z`. Too many zombies = a parent that never calls wait.

**Orphan**: a child whose parent died first. It is adopted by PID 1 (the first process), which should reap it (call wait for it). This is why PID 1 matters. See section 3.3.

`[REAL]` Python fork demo. The child exits, the parent waits 0.3 seconds, then runs `ps`:

```
parent pid 17186
child: pid 17187 parent 17186
  PID  PPID STAT COMM
17187 17186 Z    <defunct>          <-- zombie: finished, not yet reaped
reaped, exit code = 7
I am now the echo program, same pid: 17190    <-- exec: same PID, new program
```

### 3.2 Signals

A signal is a tiny message to a process. The common ones:

| Signal | Number | Meaning | Can the program catch it? |
|---|---|---|---|
| SIGHUP | 1 | "terminal closed" (many daemons reload config) | yes |
| SIGINT | 2 | Ctrl-C | yes |
| SIGQUIT | 3 | Ctrl-\ , quit with core dump | yes |
| SIGKILL | 9 | kill now, no cleanup | **no** |
| SIGTERM | 15 | polite "please stop" (the default of `kill`) | yes |
| SIGSTOP | 19 on Linux | pause | **no** |
| SIGCHLD | 17 on Linux | a child changed state | yes |

(`kill -l` prints the list for your OS. On Linux SIGSTOP is 19 and SIGCHLD is 17; on macOS the numbers differ. That is why people write names, not numbers.)

`[REAL]` `kill -l` on this Mac:
```
HUP INT QUIT ILL TRAP ABRT EMT FPE KILL BUS SEGV SYS PIPE ALRM TERM URG STOP TSTP CONT CHLD ...
```

**Graceful shutdown**: when Kubernetes stops a pod it sends SIGTERM, waits (30 seconds by default, the "grace period"), then sends SIGKILL. A good app catches SIGTERM, finishes current requests, closes connections, then exits.

**Exit code from a signal**: a shell shows `128 + signal number`. SIGKILL is 9, so 137. SIGTERM is 15, so 143. You will see **137** in Kubernetes when a container was killed (often by the OOM killer).

`[REAL]`
```
got signal 15 (SIGTERM) - cleaning up          <-- a handler caught SIGTERM
SIGKILL cannot be caught:
  error: [Errno 22] Invalid argument           <-- the OS refuses a handler for SIGKILL
child killed by SIGKILL -> python returncode -9 ; shell would show 137
```

### 3.3 PID 1 is special

PID 1 is the first process. On a normal Linux host it is `systemd` (or `init`). On macOS it is `launchd`:

`[REAL]`
```
  PID  PPID STAT ELAPSED COMMAND
    1     0 Ss     26:22 /sbin/launchd
```

PID 1 has two special jobs:
1. It **adopts orphans** and reaps them (calls wait), so zombies do not pile up.
2. The kernel protects it: a signal with no handler is **ignored** for PID 1 (a normal process would die). So if your app is PID 1 in a container and does not install a SIGTERM handler, `docker stop` or a pod delete will **not** stop it. It waits for the grace period and then gets SIGKILL.

Docker's own docs describe `--init` this way: it "forwards signals and reaps processes" (see Sources). More in file 03.

### 3.4 File descriptors (fd)

Every process has a table of open things. Numbers 0, 1, 2 are always there:

```
0 = stdin   (input)
1 = stdout  (normal output)
2 = stderr  (error output)
3, 4, 5 ... = files, sockets, pipes you open
```

Rule: a new open gets the **lowest free number**. A network connection also uses one fd. Each process has a limit (`ulimit -n`). If you hit it you get the error **"Too many open files"** (error name EMFILE). Usual cause: a program opens files or connections and never closes them (a "leak").

`[REAL]`
```
fds at start: 0=stdin 1=stdout 2=stderr
open('/etc/hosts') got fd 3
second open got fd 4
dup2 copied fd 3 to 10
closed first; next open gets lowest free fd -> 3     <-- lowest free number is reused
```
`[REAL]` `ulimit -n` on this Mac says `1048576`. On many Linux systems the default soft limit is 1024 for a normal shell, so check with `ulimit -n`. (Not verified here; it depends on the distro and on systemd/container settings.)

### 3.5 Memory: virtual memory, page cache, "available"

Each process thinks it has its own big private memory. That is **virtual memory**. The kernel maps it to real RAM in small pieces called **pages**. The kernel docs say virtual memory "abstracts the details of physical memory from the application software".

**Page cache**: when you read a file, the kernel keeps its pages in RAM. The next read is fast (no disk). When you write, the page is marked **dirty** and written to disk a bit later. The man page defines Cached as "In-memory cache for files read from the disk (the page cache)" and Dirty as "Memory which is waiting to get written back to the disk."

So "free" RAM being small is **normal and healthy**. Linux uses spare RAM as cache and gives it back when a program needs it.

**MemFree vs MemAvailable** (from `/proc/meminfo`, a fake file where the kernel shows its numbers):
- `MemFree` = RAM that is completely unused.
- `MemAvailable` = "An estimate of how much memory is available for starting new applications, without swapping" (man page). It counts memory the kernel can take back easily, like clean cache.

**Always look at `available`, not `free`.**

```
 +--------------------------- total RAM ---------------------------+
 | used by programs | page cache (clean, can drop) | free |   ...   |
 +------------------+------------------------------+------+---------+
                    \______ reclaimable _____/      \ unused /
 available  ≈  free + the reclaimable part
```

Not all cache can be dropped. `Shmem` (tmpfs, shared memory) counts as "cache" in some tools but cannot just be freed ("Amount of memory consumed in tmpfs(5) filesystems, System V, and POSIX shared memory").

`[SAMPLE]` `free -h` on Linux (made-up numbers):
```
               total        used        free      shared  buff/cache   available
Mem:            15Gi       3.1Gi       412Mi       120Mi        11Gi        11Gi
Swap:          2.0Gi          0B       2.0Gi
```
Only 412 Mi "free", but 11 Gi "available". The machine is fine.

`[REAL]` macOS has no `free`. `vm_stat` shows pages (here one page is 16384 bytes):
```
Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                     6460.
Pages active:                                 436850.
Pages inactive:                               432240.
```
Same lesson: "free" is tiny on a healthy Mac too.

### 3.6 The OOM killer

OOM = **O**ut **O**f **M**emory. When memory is full and the kernel cannot free enough, it picks a process and kills it to save the system. The kernel docs say: "In order to save the rest of the system, it invokes the OOM killer."

Steps:
1. Programs ask for more memory.
2. Kernel first reclaims: drops clean cache, writes dirty pages, swaps out (moves rarely used pages to disk).
3. If that is not enough, the OOM killer picks the "worst" process (biggest memory use, adjusted by a score) and sends SIGKILL.
4. The process dies with no warning. You see exit code 137. The kernel log has a line like "Out of memory: Killed process ...".

**In containers**: a cgroup (a group with limits, file 03) has its own memory limit (`memory.max`). When the group hits the limit and cannot reclaim, the OOM killer runs **inside that group**. The kernel doc: `memory.max` is the "Memory usage hard limit", and `memory.events` has an `oom_kill` counter. In Kubernetes this is the `OOMKilled` state. Important: the **node** can have lots of free memory and your container still gets killed, because the container hit **its own** limit.

`[SAMPLE]` how to see it on a Linux host:
```
$ dmesg -T | grep -i "killed process"
[Sun Nov 15 21:40:11 2026] Out of memory: Killed process 4242 (java) total-vm:9123456kB, anon-rss:7123456kB ...
$ journalctl -k | grep -i oom        # same on systemd machines
```
(`dmesg` may need root on some systems. The exact wording changes between kernel versions.)

### 3.7 Inodes, hard links, symlinks

A directory is a table: name -> inode number. The inode holds the file facts and block locations.

```
 directory entry        inode 99415                data blocks
 "hosts"  ---------->  [size, owner, perms,  ---->  [the bytes]
                         link count = 1]
```

- **Hard link**: another name for the same inode. The link count goes up. The data is deleted only when the link count is 0 **and** no process still has it open.
- **Symlink** (symbolic link): a tiny file that holds a path. If the target is removed, the symlink is "broken".

`[REAL]`
```
$ echo hello > a.txt; ln a.txt b.txt; ln -s a.txt c.txt; ls -li a.txt b.txt c.txt
16946503 -rw-r--r--@ 2 user  wheel  6 Nov 15 21:15 a.txt     <-- same inode 16946503,
16946503 -rw-r--r--@ 2 user  wheel  6 Nov 15 21:15 b.txt     <-- link count 2
16946506 lrwxr-xr-x@ 1 user  wheel  5 Nov 15 21:15 c.txt -> a.txt   <-- own inode, points to a name
$ rm a.txt; cat b.txt; cat c.txt
hello                                      <-- data still alive through b.txt
cat: c.txt: No such file or directory      <-- symlink is now broken
```

**Inode exhaustion**: a Linux filesystem like ext4 makes a fixed number of inodes when it is created. Millions of tiny files can use them all. Then you cannot create files even though `df -h` shows free space. Check with `df -i`.

`[REAL]` `df -i /` (this Mac uses APFS, which does not have a fixed inode count, so it shows 0% used):
```
Filesystem        Size    Used   Avail Capacity iused ifree %iused  Mounted on
/dev/disk3s3s1   460Gi    12Gi   362Gi     4%    459k  3.8G    0%   /
```

### 3.8 df vs du (why "disk full" but nothing big is found)

- `df` asks the **filesystem**: "how many blocks are used?" It is the truth about space.
- `du` **walks the directories** and adds up file sizes it can see.

They disagree when:
1. **A deleted file is still open.** You `rm` a big log, but a process still holds it open. The name is gone (du cannot see it) but the blocks stay until the process closes it or dies. This is the #1 interview answer.
2. Files hidden under a **mount point** (a disk mounted on top of a folder that already had files).
3. Reserved blocks, snapshots, or filesystem metadata.
4. Inode exhaustion (`df -h` fine, `df -i` full).

`[REAL]` proof of case 1. A program wrote 20 MB, then the file was removed. `lsof` still lists it, and the link count is 0:
```
file removed from directory (ls cannot see it): False
COMMAND   PID          USER   FD   TYPE  DEVICE SIZE/OFF     NODE NAME
Python  17194 user   3w   REG    1,13 20000000 16946499 /private/tmp/.../big.bin
link count of open fd: 0 size: 20000000
```
Fix on Linux: `lsof +L1` (lists open files with link count < 1) to find the process, then restart it, or truncate through its fd: `: > /proc/<pid>/fd/<n>`.

`[REAL]` `du -sh /usr/bin` -> `80M	/usr/bin` and `df -h /` shows 460Gi size, 12Gi used.

### 3.9 Writing data safely: fsync and atomic rename

When a program "writes" a file, the data usually goes to the page cache first. If the power fails now, the data can be lost. `fsync(fd)` tells the kernel: write this file's data to the storage device **now**, and wait until the device says done. The man page says it flushes so the data can be "retrieved even if the system crashes or is rebooted".

Careful: `fsync` on the file does **not** guarantee that the **directory entry** (the name) is on disk. The man page says you need to `fsync` the directory too.

`rename(old, new)` is **atomic** on the same filesystem: other programs see either the old file or the new file, never a half-written one. The man page: if the new path exists it "will be atomically replaced". It fails with `EXDEV` if the two paths are on different mounts.

So the safe way to update a config file:

```
1. write new content to a TEMP file in the SAME directory
2. fsync the temp file          (data is on disk)
3. rename temp -> real name     (atomic swap)
4. fsync the directory          (the new name is on disk)
```

`[REAL]` Python version. The inode number changes, because the new file replaced the old one:
```
wrote .../config.json inode 16946501
wrote .../config.json inode 16946502
{"v":2}
```
Why interviewers like it: it explains how databases, editors, and tools like Terraform's state writes avoid corrupt files. It also explains why ConfigMap updates in Kubernetes use a symlink swap (an atomic switch).

## 4. Commands to try

Safe, read-only. Linux versions first where they differ.

```bash
# processes
ps aux                      # all processes (Linux and Mac)
ps -o pid,ppid,stat,comm -p $$      # this shell: PID, parent, state, name
pstree -p            # tree view (Linux; on Mac: brew install pstree)
top                  # live view; press 1 for per-CPU, M sort by memory (Linux top)
kill -TERM <pid>     # polite stop        kill -KILL <pid>   # force

# file descriptors and what a process has open
ls -l /proc/<pid>/fd         # Linux only
lsof -p <pid>                # Linux and Mac
lsof -nP -iTCP -sTCP:LISTEN  # who is listening on which TCP port
ulimit -n                    # fd limit of this shell

# memory (Linux)
free -h
grep -E 'MemTotal|MemFree|MemAvailable|^Cached|Dirty|Shmem' /proc/meminfo
cat /proc/<pid>/status | grep -E 'VmRSS|VmSize'
dmesg -T | grep -i -E 'oom|killed process'

# disk and inodes
df -h        df -i
du -sh /var/log/* | sort -h | tail
ls -li file          # show inode number
stat file            # inode, links, size, times
lsof +L1             # open files that were deleted
```

`[SAMPLE]` `/proc/meminfo` lines on Linux:
```
MemTotal:       16384000 kB
MemFree:          421000 kB
MemAvailable:   11400000 kB
Cached:         10800000 kB
Dirty:              1200 kB
Shmem:            123000 kB
```

## 5. Common mistakes

1. Reading "free" memory as "memory left". Use `available`.
2. Thinking `kill` always kills. Default is SIGTERM, which a program may ignore. Only SIGKILL cannot be ignored.
3. Using `kill -9` first. The process gets no chance to clean up (half-written files, locks left behind).
4. Running a shell script as PID 1 in a container with `CMD ./start.sh`: the shell does not pass SIGTERM to the app. Use `exec ./app` at the end of the script, or an init like `tini`.
5. Deleting a big log file and expecting free space while the process still holds it open.
6. Forgetting inodes: "No space left on device" but `df -h` shows space.
7. Writing config in place (open, truncate, write). A crash in the middle leaves a broken file. Use temp + rename.
8. Believing `fsync` on the file also saves its name. It does not (directory needs its own fsync).

## 6. Eight interview questions with answers

**Q1. What happens when you run `ls` in a shell?**
The shell calls `fork()` to make a child copy of itself. The child calls `exec()` to become the `ls` program. The shell calls `wait()` and sleeps until `ls` finishes. `ls` writes to fd 1 (stdout). When it exits, the shell reads the exit code, shows the next prompt.

**Q2. What is a zombie process? How do you remove one?**
A zombie is a child that has exited but whose parent has not called `wait()`. It uses no CPU or memory, only a slot in the process table. You cannot kill it (it is already dead). You fix the parent: make it call wait, or restart the parent. When the parent dies, PID 1 adopts the zombie and reaps it.

**Q3. SIGTERM vs SIGKILL?**
SIGTERM (15) asks the program to stop; the program can catch it and clean up. SIGKILL (9) is handled by the kernel; the program cannot catch, block, or ignore it. Use SIGTERM first, SIGKILL last. In Kubernetes: SIGTERM, wait for the grace period (default 30 s), then SIGKILL.

**Q4. Why does my container ignore `docker stop` and take 10 seconds (or 30 in Kubernetes) to stop?**
The app is probably PID 1. PID 1 gets no default signal actions from the kernel, so SIGTERM with no handler is ignored. Docker waits the timeout, then sends SIGKILL. Fixes: handle SIGTERM in the app, use `exec` in start scripts, and/or run with `--init` (a tiny init such as tini that forwards signals and reaps zombies).

**Q5. A server shows 200 MB "free" but is fine. Why? What do you look at?**
Linux uses spare RAM as page cache, so "free" is small by design. Look at `MemAvailable` (`free -h` column `available`): an estimate of memory for new programs without swapping. Also watch swap activity, major page faults, and OOM messages.

**Q6. `df` says 100% full but `du` adds up to much less. What are the causes?**
Most common: a deleted file still open by a process. Find it with `lsof +L1`, restart the process (or truncate via `/proc/PID/fd/N`). Others: files under a mount point, reserved blocks, snapshots. Also check `df -i` for inode exhaustion.

**Q7. What is an inode? What is the difference between a hard link and a symlink?**
An inode stores a file's metadata and the location of its data. The name lives in the directory and points to the inode. A hard link is another name for the same inode (link count goes up; data is freed when count is 0 and no one has it open). A symlink is a separate small file that stores a path; it breaks if the target goes away. Hard links cannot cross filesystems; symlinks can.

**Q8. How do you update a file so a crash cannot leave it half-written?**
Write a temp file in the same directory, `fsync` it, `rename()` it over the real name (atomic on one filesystem), then `fsync` the directory. Readers see the old or the new file, never a mix.

## 7. Self-quiz (answers at the end)

1. What is the difference between `fork` and `exec`?
2. A container is killed with exit code 137. Which signal was it, and what is one likely cause?
3. Which number in `free -h` tells you how much memory new programs can get, and why not `free`?
4. You delete a 50 GB log and `df` does not change. What is your first command?
5. Why does the temp file for an atomic write have to be in the same directory (same filesystem)?

**Answers**
1. fork copies the process (new PID). exec replaces the running program inside a process (same PID).
2. 137 = 128 + 9 = SIGKILL. A likely cause is the OOM killer (the container hit its memory limit). It can also be a grace-period kill after SIGTERM was ignored.
3. `available`. `free` counts only totally unused RAM and ignores reclaimable cache.
4. `lsof +L1` (find the process holding the deleted file), then restart it.
5. `rename()` is atomic only inside one filesystem. Across mounts it fails with EXDEV, and a copy would not be atomic.

## 8. Sources

- proc_meminfo(5), definitions of MemFree, MemAvailable, Cached, Dirty, Shmem: https://man7.org/linux/man-pages/man5/proc_meminfo.5.html
- Kernel docs, memory concepts (virtual memory, page cache, reclaim, OOM killer): https://docs.kernel.org/admin-guide/mm/concepts.html
- Kernel docs, cgroup v2 (`memory.max`, `memory.events oom_kill`): https://docs.kernel.org/admin-guide/cgroup-v2.html
- fsync(2): https://man7.org/linux/man-pages/man2/fsync.2.html
- rename(2): https://man7.org/linux/man-pages/man2/rename.2.html
- Docker `run` reference (`--init`): https://docs.docker.com/reference/cli/docker/container/run/
- Kubernetes, resource limits and OOM kills: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

Not verified from a source (general Linux knowledge, check on your machine): default `ulimit -n` of 1024 on many distros; exact `dmesg` wording; the `lsof +L1` and `/proc/PID/fd` truncation trick; signal numbers 17 and 19 on Linux; "copy-on-write" detail of fork; the kernel's rule that PID 1 ignores unhandled signals (the Docker doc supports the effect, not the kernel source).

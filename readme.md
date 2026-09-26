# qBittorrent quick migration script

## Is for

When you want to migrate one platform's qBt installation's downloaded(/downloading?) torrents to another platform's, but not move the files themselves, just make the target qBt installation locate them in a different path with the same relative structure.

## Does what

1. Takes an input directory with *.fastresume files (usually your BT_Backup dir).
2. Parses the files and collects their download paths per the `save_path` key.
   * It deduplicates the paths while doing this, meaning: if you have several torrents on the same dir, they will be grouped together and their paths have the exact same replacement value. This is a quick KISS system migration tool, mainly meant for going between windows and linux, not for moving the actual torrents content, hence the assumption that torrents won't be on the same relative place is beyond its scope.
3. Lists the (unique) collected paths.
4. Prompts for a replacement path for each collect path
   * If you use an input file, you'll only be prompted for the confirmation step (5)
5. Prompts for confirmation and gives opportunity to manually change (in cli input) any of the queued replacements.
6. Writes the changed *.fastresume files to the output directory (which is whatever CWD if none specified, or the same input directory, if manually specified by path, or by `--inplace` flag) the changed files
   * Also attempts to copy all the *.torrent files found in the input directory to the output directory. The copy is indiscriminate (doesn't verify for same-name .torrent and .fastresume'), non-recursive, and filtered only by leaf extension. Whether the appropriate files are in the appropriate dir is your business, not mine :P.

## Choose because

* Zero non-builtin dependencies.
* No twiddling around with package management.
* It's just a file that you download and needs nothing more than the very Python you need to run it at all in the first place.
* Does one thing and does it good enough for my use-case, and likely yours too. (If something breaks for your use-case, file an issue. If you know the solulu and can file a PR, do so. Heck, paste the fix code in the issue itself for all I care :y/).

## Usage

### CLI

| Argument | Details |
|---|---|
| `[first positional argument]`  or specified with `-d` or `--input-dir` | Directory from which to read the .fastresume and .torrent files.
|`[second positional argument]` or specified with `-o` or `--output-dir`| Directory to which write the resulting files. If not specified defaults to whatever `os.getcwd()` returns, unless `inplace` is specified.|
|`-f` or `--input-file`| Specifies a file that has one path-pair per line, composed of the paths to modify and their replacements with a separator inbetween. Default is a pipe `\|` character but you can change `PATH_PAIRS_SEPARATOR` at the top of the file to your personal preference. The script will report (and ignore for any modifications) the paths that are specified in this file and not found among the ones collected in the .fastresume files, and also the ones that are in the .fastresume files, but not specified in this input file.|
|`-i` or `--inplace`| Just modify the .fastresume files in place instead of copying them to an output dir.|

### Module

Throw `from qbtqm import convert_fastresume_dir` into your pyhton file to have the relevant functionality, you probably know what to do from there.

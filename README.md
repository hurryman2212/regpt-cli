# regpt-cli

regpt-cli is the executable RestAPI frontend for [the OpenAI Website](https://chat.openai.com) using [reverse-engineered-chatgpt](https://github.com/Zai-Kun/reverse-engineered-chatgpt) as the backend.

## Usage

```sh
regpt-cli -h
```

## TODO

- [ ] Add arguments for the system prompt(s)
- [ ] Fix prompt's `EOFError` & `KeyboardInterrupt` handling
  - [ ] Linux
  - [ ] Windows
  - [ ] MacOS
- [ ] Prompt separation point other than '\n'
- [ ] Per-'\n' formatting with more arguments
- [ ] Enhance the method to retrieve the latest cookie(s) (+ User-Agent/etc.) we need
  - [ ] Implement cookie caching (if needed)
  - [ ] Support more browser types (if needed)
  - [ ] Confirm MacOS support
  - [ ] Cookie (+ User-Agent/etc.) override with 'KEY:VALUE [KEY:VALUE ...]'-style argument
- [ ] Output confirmation mode (print to stderr (or specific file/pipe/?) & ask for confirmation before printing to stdout) - need to clear the previous output
- [ ] Show (a) content(s) other than plain text via (a) separate window(s) (or, render within the same terminal interface with possible limitations?) (if the backend supports)
- [ ] Modularize to make it suitable as a library module
- [ ] Interface for bringing up previous conversations and selecting one of them to continue
- [ ] Use the default configuration file (of which default name (path) is ?) & add an argument to skip it
- [ ] Add fancy stuff like logging, and fancy input/output formatting including Markdown (+ arguments to control those), etc.

#!/usr/bin/env python3

import argparse, asyncio, glob, os, platform, shutil, sqlite3, sys, tempfile

from enum import StrEnum
from pathlib import Path
from re_gpt import AsyncChatGPT
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service


class browser_type(StrEnum):
    firefox = "firefox"


class flush_method(StrEnum):
    buffer = "buffer"
    no = "no"
    yes = "yes"


def decode_escape(string: str) -> str:
    return string.encode().decode("unicode-escape") if string else ""


def flush_print(string: str = ""):
    print(string, end="", flush=True)


def firefox_get_site_cookies(profile_dir: str, host: str):
    cookies_path = os.path.join(profile_dir, "cookies.sqlite")
    with (
        open(cookies_path, "rb") as cookies_file,
        tempfile.NamedTemporaryFile(delete=False) as tmp_file,
    ):
        tmp_filename = tmp_file.name

        tmp_file.write(cookies_file.read())
        cookies = []
        for host, path, isSecure, expiry, name, value in (
            sqlite3.connect(tmp_filename)
            .cursor()
            .execute(
                "SELECT host, path, isSecure, expiry, name, value FROM moz_cookies WHERE host = ? OR host = ?",
                (f".{host}", host),
            )
            .fetchall()
        ):
            cookies.append(
                {
                    "host": host,
                    "path": path,
                    "isSecure": isSecure,
                    "expiry": expiry,
                    "name": name,
                    "value": value,
                }
            )

    Path.unlink(tmp_filename)
    return cookies


async def regpt_cli(
    session_token: str,
    conversation_id: str = None,
    flush_method: flush_method = flush_method.no,
    iterative: bool = False,
    model: str = "gpt-3.5",
    postfix_assistant: str = None,
    postfix_user: str = None,
    prefix_assistant: str = None,
    prefix_user: str = None,
    print_prompt: bool = False,
):
    async with AsyncChatGPT(session_token=session_token) as chatgpt:
        while True:
            try:
                prompt = ""
                if not os.isatty(sys.stdin.fileno()):
                    prompt = sys.stdin.read(1)
                    if prompt == "":
                        raise EOFError
                prompt += input(decode_escape(prefix_user))
            except (EOFError, KeyboardInterrupt):
                break
            if print_prompt:
                print(prompt, end="")
            flush_print(decode_escape(postfix_user))

            if conversation_id:
                conversation = chatgpt.get_conversation(conversation_id)
            else:
                conversation = chatgpt.create_new_conversation(model)

            flush_print(decode_escape(prefix_assistant))
            content_buffer = ""
            if flush_method == flush_method.buffer:
                async for message in conversation.chat(prompt):
                    content_buffer += message["content"]
                flush_print(content_buffer)
            else:
                async for message in conversation.chat(prompt):
                    print(
                        message["content"],
                        flush=True if flush_method == flush_method.yes else False,
                        end="",
                    )
            flush_print(decode_escape(postfix_assistant))

            conversation_id = conversation.conversation_id
            if not iterative:
                break

    return conversation_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-b",
        "--browser",
        choices=[e for e in browser_type],
        default="firefox",
        help="browser to use for cookie generation",
        type=browser_type,
    )
    parser.add_argument(
        "-i",
        "--iterative",
        action="store_true",
        help="use iterative chat",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="gpt-3.5",
        help="OpenAI model to use",
        type=str,
    )

    parser.add_argument(
        "--flush-method",
        choices=[e for e in flush_method],
        default="no",
        help="flush method of assistant's output",
        type=flush_method,
    )
    parser.add_argument(
        "--postfix-assistant",
        help="postfix to print after each assistant response",
        type=str,
    )
    parser.add_argument(
        "--postfix-user",
        help="postfix to print after each user prompt",
        type=str,
    )
    parser.add_argument(
        "--prefix-assistant",
        help="prefix to print before each assistant response",
        type=str,
    )
    parser.add_argument(
        "--prefix-user",
        help="prefix to print before each user prompt",
        type=str,
    )
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="print input prompt(s) as well",
    )

    args = parser.parse_args()

    match args.browser:
        case "firefox":
            system = platform.system()
            system_path = (
                "Appdata/Roaming/Mozilla/Firefox/Profiles"
                if system == "Windows"
                else (
                    "Library/Application Support/Firefox/Profiles"
                    if system == "Darwin"
                    else ".mozilla/firefox"
                )
            )
            profile_dir = glob.glob(
                f"{str(Path.home())}/{system_path}/*.default-release"
            )[0]
            options = Options()
            if system == "Windows":
                options.binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
            options.add_argument("-headless")
            driver = webdriver.Firefox(
                options=options,
                service=Service(
                    shutil.which("geckodriver"), log_output=open(os.devnull, "w")
                ),
            )

    driver.get("https://chat.openai.com")
    for cookie in firefox_get_site_cookies(profile_dir, "chat.openai.com"):
        driver.add_cookie(cookie)

    driver.get("https://chat.openai.com")
    session_token = [
        d["value"]
        for d in driver.get_cookies()
        if d.get("name") == "__Secure-next-auth.session-token"
    ][0]

    if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(
        regpt_cli(
            session_token,
            flush_method=args.flush_method,
            iterative=args.iterative,
            model=args.model,
            postfix_assistant=args.postfix_assistant,
            postfix_user=args.postfix_user,
            prefix_assistant=args.prefix_assistant,
            prefix_user=args.prefix_user,
            print_prompt=args.print_prompt,
        )
    )

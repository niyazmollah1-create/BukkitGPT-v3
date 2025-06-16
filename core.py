import os
import uuid
import shutil
import queue

import build
import config
import utils
from log_writer import logger

# Re-export utility functions for backward compatibility
initialize = utils.initialize
askgpt = utils.askgpt
response_to_action = utils.response_to_action
mixed_decode = utils.mixed_decode
decompile_jar = utils.decompile_jar
code_to_text = utils.code_to_text
parse_edit_response = utils.parse_edit_response
apply_diff_changes = utils.apply_diff_changes


def generate(args: dict, output_queue: queue.Queue = None) -> bool:
    """Generate a new plugin using the provided arguments."""
    name = args["PluginName"].get()
    description = args["PluginDescription"].get()

    artifact_name = name.replace(" ", "")
    package_id = f"dev.cynia.{uuid.uuid4().hex[:8]}"
    pkg_id_path = "".join(id + "/" for id in package_id.split("."))

    logger(f"user_input -> name: {name}")
    logger(f"user_input -> description: {description}")
    logger(f"random_generate -> package_id: {package_id}")
    logger(f"str_path -> pkg_id_path: {pkg_id_path}")

    if output_queue:
        output_queue.put("Generating plugin...")
    else:
        print("Generating plugin...")

    codes = askgpt(
        config.SYS_GEN.replace("%ARTIFACT_NAME%", artifact_name).replace(
            "%PKG_ID_LST%", pkg_id_path
        ),
        config.USR_GEN.replace("%DESCRIPTION", description),
        config.GENERATION_MODEL,
    )
    logger(f"codes: {codes}")

    response_to_action(codes)

    if output_queue:
        output_queue.put("Code generated. Building now...")
    else:
        print("Code generated. Building now...")

    result = build.build_plugin(artifact_name, output_queue=output_queue)

    target_dir = f"codes/{artifact_name}/target"
    jar_files = [f for f in os.listdir(target_dir) if f.endswith('.jar')]

    if jar_files:
        message = f"Build complete. Find your plugin at '{target_dir}/{jar_files[0]}'"
        if output_queue:
            output_queue.put(message)
        else:
            print(message)
    else:
        error_message = (
            "Build failed. This is because the code LLM generated has syntax errors. "
            "Please try again or switch to a better LLM like o1 or r1. IT IS NOT A BUG OF BUKKITGPT."
        )
        if output_queue:
            output_queue.put(error_message)
        else:
            print(error_message)

    return True


def edit(args: dict, output_queue: queue.Queue = None) -> bool:
    """Edit an existing plugin according to the user's request."""
    original_jar = args["OriginalJAR"].get()
    edit_request = args["EditRequest"].get()

    decompiled_path = f"codes/decompiled/{original_jar.split('/')[-1].split('.')[0]}"

    decompile_jar(original_jar, decompiled_path)

    os.makedirs(f"{decompiled_path}/src/main/java", exist_ok=True)

    summary_path = os.path.join(decompiled_path, "summary.txt")
    if os.path.exists(summary_path):
        os.remove(summary_path)

    for item in os.listdir(decompiled_path):
        if item != 'src':
            s = os.path.join(decompiled_path, item)
            d = os.path.join(decompiled_path, "src/main/java", item)
            if os.path.isdir(s):
                shutil.move(s, d)
            elif os.path.isfile(s):
                shutil.move(s, d)

    with open(f"{decompiled_path}/pom.xml", "w") as f:
        f.write("<!-- Replace with the pom.xml code -->")

    code_text = code_to_text(decompiled_path)
    response = askgpt(
        config.SYS_EDIT,
        config.USR_EDIT.replace("ORIGINAL_CODE", code_text).replace("REQUEST", edit_request),
        config.GENERATION_MODEL,
    )

    diffs = parse_edit_response(response)
    logger(f"[DEBUG] Extracted diffs: {diffs}")

    resp = apply_diff_changes(diffs, decompiled_path)

    if resp[0] is False:
        error_message = (
            "The diff LLM generated is invalid. Please try again or switch to a better LLM like o1 or r1. IT IS NOT A BUG OF BUKKITGPT."
        )
        if output_queue:
            output_queue.put(error_message)
        else:
            print(error_message)
    else:
        if output_queue:
            output_queue.put("Edit complete. Recompiling...")
        else:
            print("Edit complete. Recompiling...")
            
        result = build.build_plugin(decompiled_path, path=True, output_queue=output_queue)
        target_dir = f"{decompiled_path}/target"
        jar_files = [f for f in os.listdir(target_dir) if f.endswith('.jar')]

        if jar_files:
            message = f"Build complete. Find your plugin at '{target_dir}/{jar_files[0]}'"
            if output_queue:
                output_queue.put(message)
            else:
                print(message)
        else:
            error_message = (
                "Build failed. This is because the code LLM generated has syntax errors. "
                "Please try again or switch to a better LLM like o1 or r1. IT IS NOT A BUG OF BUKKITGPT."
            )
            if output_queue:
                output_queue.put(error_message)
            else:
                print(error_message)

    return True


"""Run a Python student program without network or child processes."""
import runpy
import sys


def deny(event, args):
    if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto", "subprocess.Popen", "os.system", "os.posix_spawn"}:
        raise PermissionError("Offline grader blocked: " + event)
    if event == "socket.bind" and isinstance(args[1], tuple):
        raise PermissionError("Offline grader blocked TCP/UDP bind")


if __name__ == "__main__":
    sys.addaudithook(deny)
    script = sys.argv.pop(1)
    sys.path.insert(0, str(__import__("pathlib").Path(script).resolve().parent))
    runpy.run_path(script, run_name="__main__")

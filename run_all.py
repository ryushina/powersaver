# run_all.py
import subprocess, sys, atexit

procs = []

def launch(script):
    p = subprocess.Popen([sys.executable, "-u", script])
    procs.append(p)
    return p

def shutdown():
    for p in procs:
        p.terminate()

if __name__ == "__main__":
    atexit.register(shutdown)
    launch("tapo_fire.py")
    # Block on main app; when it exits, atexit will terminate the worker
    subprocess.call([sys.executable, "-u", "main.py"])

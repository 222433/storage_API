# run.py
import uvicorn
import pathlib
import sys
import debugpy
debug_port=5679
debugpy.listen(("0.0.0.0", debug_port))
print('debugging on port {} started'.format(debug_port))
if __name__ == "__main__":
    sys.path.append(str(pathlib.Path(__file__).parent))
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=False)

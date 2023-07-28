from lib import csDetector, logger
import sys

if __name__ == "__main__":
    logger = logger.Logger()
    inputData = sys.argv[1:]
    tool = csDetector.CsDetector()
    results = tool.executeTool(inputData)

    # print results
    for r in results:
        (_, formated) = r
        for key in formated:
            print(key, formated[key])

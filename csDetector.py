from csDetector import csDetector
import sys

if __name__ == "__main__":
    inputData = sys.argv[1:]
    tool = csDetector()
    formattedResults, results, config = tool.executeTool(inputData)
    print(results)
    print(formattedResults)

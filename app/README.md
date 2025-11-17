# Docker enviroment options:

DOMAIN -> (default: localhost)
PORT -> (default: 5173)
FLASK_RUN_HOST -> define the host on which the Flask app will run. (default: 0.0.0.0)
FLASK_RUN_PORT -> define the port on which the Flask app will run. (default: 8080)
ORIGINS -> allowed origins for CORS. (default: "*")
MAX_ENTRIES -> limit the number of entries to process when testing. (default: all)
CUDA -> whether CUDA should be used for SpliceAI. (default: false)
CUDA_BATCH_SIZE -> CUDA batch size for SpliceAI. (default: 32)


# Example command for running on x86 hardware:

docker run --restart always --name kathAIO -it --rm -p 8080:8080 -p 5173:5173 -e DOMAIN={server-IP} -v /data/:/kath/app/back_end/src/workspace/ cpu64/kath:final-amd64-fixed

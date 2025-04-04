STATUS: [[Not-Integrated]]

[Repo](https://github.com/google-deepmind/alphamissense)

**Purpose**: [[AI model]] that predicts whether genetic mutations in proteins are likely to be harmless or disease-causing.

**Online**: No, unless we use Online tools such a Google Colab

Can benefit from HPC: GPU-accelerated/Can be updated to have profit from [[GPU]] acceleration

**Can run localy**: Yes, but can also be run on Google Colab, which provides acess to GPUs and other computing resources: https://colab.research.google.com/github/tkzeng/Pangolin/blob/main/PangolinColab.ipynb

**Can run on KTU-compute**: Needs to. The tool is a neural net, but the weights are not set so it needs be trained. You can find certain predictions that they already made on the cloud, but they seem not related to our project.

**Required resources**: The publicly available resources don't suggest any specific requirements, but based on the source code available on GitHub and the libraries the project uses, such as JAX, dm-haiku, and ml-collections, which are mostly GPU-based libraries, my personal recommendation is NVIDIA graphics cards with 8-12GB VRAM. It seems like we should choose a middle range GPU from the GTX or RTX series depending on the budget. Tensor core support is a great addition to have if the JAX libraries use them in the implementation. (It doesn't seem like this tool requires Tensor tech, but I'm not 100% sure). However, we could also use tools available online. Such as Google Colab.

**Legal information**: Open source, but needs to be cited.


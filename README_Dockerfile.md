# Parent Docker images
The Dockerfile for BrainSuite BIDS App pulls a pre-compiled parent image (yeunkim/brainsuitebids:parent).

## yeunkim/brainsuitebids:parent
The Dockerfile for this pre-compiled Docker image is located in the ```parent``` branch of this repository. 
This Docker image pulls another pre-compiled parent image (yeunkim/bidsapphead). 

### yeunkim/bidsapphead
The Dockerfile for this pre-compiled Docker image, which is used by the ```yeunkim/brainsuitebids:parent``` Docker image,
is located in the ```head``` branch of this repository. 
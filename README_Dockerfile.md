# Parent Docker images
The Dockerfile for BrainSuite BIDS App pulls a pre-compiled parent image ([yeunkim/brainsuitebids:parent](https://hub.docker.com/layers/yeunkim/brainsuitebidsapp/parent/images/sha256-9381fb7e4acd0200ee771360f9bd8de7311409474d5d481dac4794125d9a8443?context=repo)) on Docker Hub.

By developing our BrainSuite BIDS App using pre-compiled images, we are able to keep the parent image the same while changing top layers of the Docker image. 
Since building Docker images pulls sources from third-party repositories, constant rebuilding can subject the Docker image to changes and risk consistency if these third party sources change.
Thus, we pull from our pre-compiled parent images which act as snapshots of version-controlled dependencies and file systems that our BrainSuite BIDS App needs. 


## yeunkim/brainsuitebids:parent
The [Dockerfile](https://github.com/bids-apps/BrainSuite/blob/parent/Dockerfile) for this pre-compiled Docker image is located in the ```parent``` branch of this repository. 
This Docker image pulls another pre-compiled parent image ([yeunkim/bidsapphead](https://hub.docker.com/layers/yeunkim/bidsapphead/latest/images/sha256-c3b033f926a472565ab61d67567a338dbc796774cb2e1d871dddceb7c7ec68a1?context=repo)). 

### yeunkim/bidsapphead
The [Dockerfile](https://github.com/bids-apps/BrainSuite/blob/head/Dockerfile) for this pre-compiled Docker image, which is used by the ```yeunkim/brainsuitebids:parent``` Docker image,
is located in the ```head``` branch of this repository. 
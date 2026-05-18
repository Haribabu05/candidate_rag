#start from the docker image that contains python 3.12 and is slim
#slim = lightweight version of the image, which is smaller in size and contains only the necessary components to run python applications.
FROM python:3.12-slim

#create a working dire called /app in the container, where we will copy our
# application code and run our commands. This helps to keep our application organized and makes it easier to manage dependencies and files within the container. By setting the working
WORKDIR /app

#copy the requirements file from the backend directory of our local machine to the working directory in the container. 
#This allows us to install the necessary dependencies for our application using pip.  
COPY backend/requirements.txt .

#install the dependencies specified in the requirements.txt file using pip.
# The --no-cache-dir option is used to prevent pip from caching the downloaded packages, which helps to reduce the size of the final image. This ensures that only the necessary dependencies are installed in the container, keeping it lightweight and efficient.

RUN pip install --no-cache-dir -r requirements.txt


#copy the contents of the backend directory from our local machine to the working directory in the container.
# This includes all the application code and files needed to run our application. By copying the backend directory, 
#we ensure that all the necessary files are available in the container for execution.

COPY backend/ .

#copy the data directory from our local machine to the working directory in the container. This allows us to include any necessary data files that our application may need to access during runtime. By copying the data directory, we ensure that all the required data is available in the container for our application to function properly.
# COPY <source> <destination>
COPY test_data/ ./data

#set the default command to run when the container starts. In this case, we specify that the container should execute the extract_pipeline.py script using the python command. This means that when the container is launched, it will automatically run the extract_pipeline.py script, allowing us to test the functionality of our application or perform any necessary operations defined in that script.
CMD ["python", "extract_pipeline.py"]
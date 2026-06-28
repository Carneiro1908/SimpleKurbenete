# Image base - Nginx Alpine
FROM nginx:alpine

# Copy the website files for nginx directory
COPY . /usr/share/nginx/html/

# Expose port 80
EXPOSE 80  

# Standart command when start container
CMD ["nginx", "-g", "daemon off;"]
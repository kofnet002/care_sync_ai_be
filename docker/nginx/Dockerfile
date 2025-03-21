FROM nginx:1.21-alpine

RUN rm /etc/nginx/conf.d/default.conf

# copy our nginx configuration to overwrite nginx defaults
COPY nginx.conf /etc/nginx/nginx.conf
COPY caresyncai.conf /etc/nginx/conf.d/caresyncai.conf

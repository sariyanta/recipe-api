server {
    listen ${LISTEN_PORT};

    location /static {
        alias /vol/static;
    }
    location/ {
        uwsgi_pass      ${APP_HOST}:${APP_PORT};
        include         /etc/nginx/uwsgi_params;
        client_body_max 10M;
    }
}
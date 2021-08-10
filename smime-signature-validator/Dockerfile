FROM public.ecr.aws/shogo82148/p5-aws-lambda:base-5.34-paws.al2
COPY handler.pl /var/task/handler.pl
COPY extlocal /var/task/extlocal
CMD [ "handler.handle" ]
import openai
# from openai import OpenAI
# client = OpenAI()

openai.api_key = "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"
fine_tuning_response = openai.FineTuningJob.create(
    # training_file=training_file_id,
    training_file="file-84IMFcIZobPcFx0CI5Tmwf3j",
    validation_file="file-xYi5LuNGfJcgo5oEOvdZqUYz",
    model="gpt-3.5-turbo-1106",
    suffix="wys20240110-1",
    # hyperparameters={
    #     "n_epochs": 4,
    #     "batch_size": 128
    # }
)
job_id = fine_tuning_response["id"]
print(fine_tuning_response)

print("获取任务ID：", job_id)

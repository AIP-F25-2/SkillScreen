from services.vocal_analytics_service import VocalAnalyticsService

analytics = VocalAnalyticsService()

# Test with dummy data
result = analytics._calculate_speaking_rate(
    transcript="I'm currently pursuing post-priced program in Artificial Intelligence and Data Science from Loyalist College Toronto. I began with Jodhni as an application development associate in Accenture where I learned to work in cross-functional teams and as well as handling large sets of volume of data. I had fully transitioned into data science domain by doing an internship with AlmaBeta where I built multiple end-to-end machine learning projects and also participated in A by V testing of their UI UX design acceptance where it increased student engagement to that platform. In my recent role as a data analyst in Quinter financial technologies, I used to build and maintain Tableau dashboards for a financial institution. Overall, I'm very pretty much excited and passionate about implementing AI solutions by utilizing Clouds technologies in order to build large scalable solutions to business. Thank you. Tell me about a computer vision project you've worked on. An interesting NLP project or computer vision project that I worked on was to classify restaurant-elp restaurant images into five classes basically food, dining, menu, inside and outside of a restaurant. These images were based on help dataset.",
    word_timestamps=[],
    duration=10.0  # 10 seconds
)

print(result)
# Should output: {"words_per_minute": 66, "pace": "slow", ...}
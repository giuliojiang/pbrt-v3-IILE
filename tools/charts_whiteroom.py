import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# IILE render -----------------------------------------------------------------

xData = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

yRenderTime = [
    20, 28, 29, 34, 42, 65, 114, 218, 447, 885, 1851
]

yEntropy = [
    1144, # 0
    1304, #1
    1312, #2
    1252, #4
    1232, #8
    1208, #16
    1192, #32
    1180, #64
    1168, #128
    1160, #256
    1160, #512
]

ySsim = [
    0.15, # 0
    0.17, #1
    0.17, #2
    0.18, #4
    0.19, #8
    0.19, #16
    0.20, #32
    0.20, #64
    0.20, #128
    0.20, #256
    0.21, #512
]

traceRenderTime = go.Scatter(
    x=xData,
    y=yRenderTime,
    name="Render time",
    yaxis="y"
)

traceEntropy = go.Scatter(
    x=xData,
    y=yEntropy,
    name="Entropy",
    yaxis="y2"
)

traceSsim = go.Scatter(
    x=xData,
    y=ySsim,
    name="Structural Similarity",
    yaxis="y3"
)

data = [traceRenderTime, traceEntropy, traceSsim]

layout = go.Layout(
    title="IILE White Room Daytime",
    xaxis=dict(
        title="Tasks",
        domain=[0.25, 0.7],
        type="log"
    ),
    yaxis=dict(
        title="seconds"
    ),
    yaxis2=dict(
        title="entropy",
        overlaying="y",
        anchor="free",
        side="left",
        position=0.15
    ),
    yaxis3=dict(
        title="similarity",
        overlaying="y",
        anchor="x",
        side="right"
    )
)

plotly.offline.plot(
    {
        "data": data,
        "layout": layout
    }
)
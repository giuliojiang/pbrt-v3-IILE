import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# IILE render -----------------------------------------------------------------

xData = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

yRenderTime = [
    20, 28, 29, 34, 42, 65, 114, 218, 447, 885, 1851
]

yEntropy = [
    11.77, # 0
    11.98, #1
    12.00, #2
    11.98, #4
    11.99, #8
    11.99, #16
    11.99, #32
    11.99, #64
    11.98, #128
    11.98, #256
    11.98, #512
] # TODO

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
] # TODO

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
        domain=[0.25, 0.7]
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
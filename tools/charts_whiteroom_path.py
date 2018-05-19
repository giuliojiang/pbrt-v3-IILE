import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# IILE render -----------------------------------------------------------------

xData = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

yRenderTime = [
    4, 7, 11, 20, 38, 73, 143, 284, 565, 1115, 2220
]

yEntropy = [
    1356, #1
    1812, #2
    1792, #4
    1724, #8
    1608, #16
    1504, #32
    1404, #64
    1276, #128
    1148, #256
    1028, #512
    916 # 1024
]

ySsim = [
    0.05, #1
    0.08, #2
    0.10, #4
    0.14, #8
    0.20, #16
    0.26, #32
    0.32, #64
    0.41, #128
    0.51, #256
    0.64, #512
    0.82, #1024
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
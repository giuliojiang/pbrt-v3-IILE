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

yPSNR = [
    176.64, #1
    181.41, #2
    185.49, #4
    190.41, #8
    196.23, #16
    201.44, #32
    207.25, #64
    213.96, #128
    221.13, #256
    228.16, #512
    235.12 # 1024
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

tracePSNR = go.Scatter(
    x=xData,
    y=yPSNR,
    name="PSNR",
    yaxis="y3"
)

data = [traceRenderTime, traceEntropy, tracePSNR]

title = "Path White Room Daytime"
xAxisLabel = "SPP"

layout = go.Layout(
    title=title,
    xaxis=dict(
        title=xAxisLabel,
        domain=[0.25, 0.7],
        type="log"
    ),
    yaxis=dict(
        title="Render time (seconds)",
        range=[0, 2500]
    ),
    yaxis2=dict(
        title="Entropy (kB)",
        overlaying="y",
        anchor="free",
        side="left",
        position=0.15,
        range=[0, 2000]
    ),
    yaxis3=dict(
        title="PSNR (dB)",
        overlaying="y",
        anchor="x",
        side="right",
        range=[170, 240]
    )
)

plotly.offline.plot(
    {
        "data": data,
        "layout": layout
    }
)
import plotly
import plotly.plotly as py
import plotly.graph_objs as go

# IILE render -----------------------------------------------------------------

xData = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

yRenderTime = [
    116, # 0
    132, #1
    133, #2
    133, #4
    138, #8
    146, #16
    165, #32
    211, #64
    289, #128
    459, #256
    793, #512
]

yEntropy = [
    876, # 0
    1188, #1
    1232, #2
    1188, #4
    1180, #8
    1168, #16
    1160, #32
    1156, #64
    1152, #128
    1148, #256
    1148, #512
]

yPSNR = [
    203.20, # 0
    208.92, #1
    209.33, #2
    209.96, #4
    210.21, #8
    210.34, #16
    210.30, #32
    210.49, #64
    210.46, #128
    210.58, #256
    210.61, #512
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

title = "IILE White Room Daytime"
xAxisLabel = "Tasks"

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
var RPCClient = require('@alicloud/pop-core').RPCClient;

function initVodClient(accessKeyId, accessKeySecret) {
  var regionId = 'cn-beijing';   // 点播服务接入地域
  var client = new RPCClient({//填入AccessKey信息
    accessKeyId: accessKeyId,
    accessKeySecret: accessKeySecret,
    endpoint: 'http://vod.' + regionId + '.aliyuncs.com',
    apiVersion: '2017-03-21'
  });

  return client;
}

// 获取 VOD 客户端（从环境变量读取凭证）
function getVodClient() {
  const accessKeyId = process.env.ALIYUN_ACCESS_KEY_ID;
  const accessKeySecret = process.env.ALIYUN_ACCESS_KEY_SECRET;
  if (!accessKeyId || !accessKeySecret) {
    throw new Error('阿里云 VOD 凭证未配置，请在 .env 中设置 ALIYUN_ACCESS_KEY_ID 和 ALIYUN_ACCESS_KEY_SECRET');
  }
  return initVodClient(accessKeyId, accessKeySecret);
}

// 获取阿里云VOD上传凭证（用于客户端直接上传到 VOD，无需经过业务服务器）
exports.getvod = async (req, res) => {
  try {
    var client = getVodClient();
    const vodback = await client.request("CreateUploadVideo", {
      Title: 'this is a sample',
      FileName: 'filename.mp4'
    }, {});
    res.status(200).json({ vod: vodback });
  } catch (error) {
    console.error('获取VOD上传凭证失败:', error);
    res.status(500).json({ error: '获取上传凭证失败' });
  }
};

// 获取视频播放信息（根据 VideoId 获取播放 URL）
exports.getPlayInfo = async (req, res) => {
  try {
    const { videoId } = req.params;
    if (!videoId) {
      return res.status(400).json({ error: '缺少视频ID' });
    }

    var client = getVodClient();
    const result = await client.request("GetPlayInfo", {
      VideoId: videoId
    }, {});

    // 解析播放信息
    const playInfoList = result.PlayInfoList?.PlayInfo || [];
    if (playInfoList.length === 0) {
      return res.status(404).json({ error: '未找到视频播放信息' });
    }

    // 按清晰度排序，优先返回高质量流
    // 清晰度优先级：OD(原画) > HD(超清) > SD(高清) > LD(标清) > FD(流畅)
    const defOrder = { 'OD': 5, 'HD': 4, 'SD': 3, 'LD': 2, 'FD': 1 };
    const sorted = playInfoList.sort((a, b) =>
      (defOrder[b.Definition] || 0) - (defOrder[a.Definition] || 0)
    );

    res.status(200).json({
      videoBase: result.VideoBase,
      playInfoList: sorted,
      // 返回默认使用的播放 URL（优先级最高的）
      defaultPlayURL: sorted[0].PlayURL,
      defaultFormat: sorted[0].Format,
      defaultDefinition: sorted[0].Definition,
    });
  } catch (error) {
    console.error('获取视频播放信息失败:', error);
    res.status(500).json({ error: '获取播放信息失败' });
  }
};

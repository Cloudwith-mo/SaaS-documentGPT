const { CloudWatchClient, PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');

const cw = new CloudWatchClient({ region: process.env.AWS_REGION || 'us-east-1' });

async function emitMetric(name, value, unit = 'Milliseconds', dims = []) {
  const params = {
    Namespace: 'DocumentGPT',
    MetricData: [
      {
        MetricName: name,
        Dimensions: dims,
        Timestamp: new Date(),
        Value: value,
        Unit: unit
      }
    ]
  };
  
  try {
    await cw.send(new PutMetricDataCommand(params));
  } catch (error) {
    console.error('Failed to emit metric:', error);
  }
}

module.exports = { emitMetric };
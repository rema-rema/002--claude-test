export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { content } = req.body;
    
    if (!content || !content.includes('!wake')) {
      return res.status(200).json({ message: 'Not a wake command' });
    }

    const githubToken = process.env.GITHUB_TOKEN;
    const githubUsername = process.env.GITHUB_USERNAME;
    const repoName = process.env.GITHUB_REPO_NAME;

    if (!githubToken || !githubUsername || !repoName) {
      return res.status(500).json({ error: 'Missing environment variables' });
    }

    const response = await fetch(`https://api.github.com/repos/${githubUsername}/${repoName}/codespaces`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Discord-Wake-Bot'
      }
    });

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const codespaces = await response.json();
    const targetCodespace = codespaces.codespaces?.[0];

    if (!targetCodespace) {
      return res.status(404).json({ error: 'No codespaces found' });
    }

    if (targetCodespace.state === 'Running') {
      return res.status(200).json({ 
        message: 'Codespace is already running!',
        name: targetCodespace.display_name 
      });
    }

    const startResponse = await fetch(`https://api.github.com/repos/${githubUsername}/${repoName}/codespaces/${targetCodespace.name}/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Discord-Wake-Bot'
      }
    });

    if (!startResponse.ok) {
      throw new Error(`Failed to start codespace: ${startResponse.status}`);
    }

    return res.status(200).json({ 
      message: `🚀 Codespace "${targetCodespace.display_name}" is starting up!`,
      codespace_url: targetCodespace.web_url
    });

  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}
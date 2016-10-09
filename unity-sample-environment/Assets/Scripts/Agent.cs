using UnityEngine;
using System.Collections.Generic;
using System.IO;
using WebSocketSharp;
using System.Threading;

namespace MLPlayer {
	public class Agent : MonoBehaviour {
		[SerializeField] int agentId;
		[SerializeField] List<Camera> rgbCameras;
		[SerializeField] List<Camera> depthCameras;
		[SerializeField] List<Texture2D> rgbImages;
		[SerializeField] List<Texture2D> depthImages;
		[SerializeField] Vector3 mygene; // add Naka
		public int Energy; // add Naka

		public Action action { set; get; }
		public State state { set; get; }

		public int GetAgentId(){
			return agentId;
		}

		public void AddReward (float reward)
		{
			if (!state.endEpisode) {
				state.reward += reward;
			}
		}

		
		public void SetGene(Dictionary<System.Object, System.Object> gene) // add Naka
		{
			// make hash table (because the 2 data arrays with equal content do not provide the same hash)
			var originalKey = new Dictionary<string, byte[]>();
			foreach (byte[] key in gene.Keys) {
				originalKey.Add (System.Text.Encoding.UTF8.GetString(key), key);
				//Debug.Log ("key:" + System.Text.Encoding.UTF8.GetString(key) + " value:" + gene[key]);
			}

			// add Naka MUST GET number of parameter
			float gene1 = float.Parse (System.Text.Encoding.UTF8.GetString((byte[])gene [originalKey ["gene1"]]));
			float gene2 = float.Parse (System.Text.Encoding.UTF8.GetString((byte[])gene [originalKey ["gene2"]]));
			float gene3 = float.Parse (System.Text.Encoding.UTF8.GetString((byte[])gene [originalKey ["gene3"]]));
			mygene = new Vector3(gene1, gene2, gene3);
		}

		public void ChangeScale() // add Naka
		{
			transform.localScale = mygene;
		}

		public void UpdateState ()
		{
			Debug.Log(Energy);
			if (Energy <= 0) {
			   this.gameObject.active = false;
			}
			state.x_s = (this.gameObject.transform.localScale.x - 3) / 3.0f;
			state.y_s = (this.gameObject.transform.localScale.y - 3) / 3.0f;
			state.z_s = (this.gameObject.transform.localScale.z - 3) / 3.0f;

			state.image = new byte[rgbCameras.Count][];
			for (int i=0; i<rgbCameras.Count; i++) {
				Texture2D txture = rgbImages [i];
				state.image[i] = GetCameraImage (rgbCameras[i], ref txture);
			}
			state.depth = new byte[depthCameras.Count][];
			for (int i=0; i<depthCameras.Count; i++) {
				Texture2D txture = depthImages [i];
				state.depth[i] = GetCameraImage (depthCameras[i], ref txture);
			}
		}
		
		public void ResetState ()
		{
			state.Clear ();
		}

		public void StartEpisode ()
		{
            int index = int.Parse(name.Substring(5)) - 1;
            SceneController.Instance.SetRawImage(index, _frameBuffer);
            this.gameObject.active = true;
	    Energy = 100;
        }

        public void EndEpisode ()
		{
			state.endEpisode = true;
		}

        void Awake()
        {
            float range_start = 1.0f;
            float range_end = 5.0f;
            mygene = new Vector3(Random.Range(range_start, range_end),
                                        Random.Range(range_start, range_end),
                                                        Random.Range(range_start, range_end));
            Energy = 100;
        }

        RenderTexture _frameBuffer;
        RenderTexture _depthBuffer;

        public void Start() {

            _frameBuffer = new RenderTexture(227, 227, 16);
            _frameBuffer.Create();
            _depthBuffer = new RenderTexture(32, 32, 24);
            _depthBuffer.Create();
       
            foreach (var c in rgbCameras)
                c.targetTexture = _frameBuffer;
            foreach (var c in depthCameras)
                c.targetTexture = _depthBuffer;

            action = new Action ();
			state             = new State ();

			rgbImages   = new List<Texture2D> (rgbCameras.Capacity);
			foreach (var cam in rgbCameras) {
				rgbImages.Add (new Texture2D (cam.targetTexture.width, cam.targetTexture.height,
					TextureFormat.RGB24, false));
			}
			depthImages = new List<Texture2D> (rgbCameras.Capacity);
			foreach (var cam in depthCameras) {
				depthImages.Add(new Texture2D (cam.targetTexture.width, cam.targetTexture.height,
					TextureFormat.RGB24, false));
			}

			foreach (var cam in depthCameras) {
				cam.depthTextureMode = DepthTextureMode.Depth;
				cam.SetReplacementShader (Shader.Find ("Custom/ReplacementShader"), "");
			}
		}


		public byte[] GetCameraImage(Camera cam, ref Texture2D tex) {
			RenderTexture currentRT = RenderTexture.active;
			RenderTexture.active = cam.targetTexture;
			cam.Render();
			tex.ReadPixels(new Rect(0, 0, cam.targetTexture.width, cam.targetTexture.height), 0, 0);
			tex.Apply();
			RenderTexture.active = currentRT;

			return tex.EncodeToPNG ();
		}
	}
}

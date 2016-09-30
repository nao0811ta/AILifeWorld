using UnityEngine;
using System.Collections;

namespace MLPlayer {
	public class State {
		public float reward;
		public bool endEpisode;
		public byte[][] image;
		public byte[][] depth;
		public byte[][] gene;  // add Naka
		public byte[] rewards; // add Naka
		public void Clear() {
			reward = 0;
			endEpisode = false;
			image   = null;
			depth   = null;
			rewards = null;
		}
	}
}